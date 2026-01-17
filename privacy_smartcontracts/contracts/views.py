from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.db import models
from .models import Contract, ContractDocument
from .forms import ContractForm, ContractDocumentForm
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
import mimetypes
from storage.utils import decrypt_bytes
from users.models import UserProfile

class OwnerOrSecondPartyRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = getattr(self, 'object', None)
        if obj is None:
            return self.request.user.is_authenticated
        return (obj.owner == self.request.user or
                obj.second_party == self.request.user or
                self.request.user.is_superuser)

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to perform this action.")
        return redirect('contracts:dashboard')

class DashboardView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'contracts/dashboard.html'
    context_object_name = 'contracts'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Contract.objects.all()
        # Show contracts owned by the user or where the user is the second_party
        return Contract.objects.filter(models.Q(owner=user) | models.Q(second_party=user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contracts = context['contracts']
        
        # Calculate statistics
        context['total_contracts'] = contracts.count()
        context['active_contracts'] = contracts.filter(status='ACTIVE').count()
        context['pending_contracts'] = contracts.filter(status='PENDING_CONFIRMATION').count()
        context['draft_contracts'] = contracts.filter(status='DRAFT').count()
        
        return context

class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/create_contract.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'owner_accepted': True} # Owner implicitly accepts on creation
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.owner_accepted = True # Owner accepts when creating the contract
        self.object = form.save(commit=True, owner=self.request.user) # No files here, handled by separate view
        messages.success(self.request, "Contract created. Pending second party confirmation.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})

class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/view_contract.html'
    context_object_name = 'contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = self.get_object()
        context['documents'] = contract.documents.all()
        context['document_form'] = ContractDocumentForm()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        
        # Allow if owner, second_party or superuser
        if self.object.owner == user or self.object.second_party == user or user.is_superuser:
            pass
        # or if public
        elif self.object.visibility == 'PUBLIC':
            pass
        # or if private and user's company is allowed
        elif self.object.visibility == 'PRIVATE':
            try:
                profile = user.userprofile
                if self.object.allowed_companies.filter(pk=profile.pk).exists():
                    pass
                else:
                    messages.error(request, "You do not have permission to view this contract.")
                    return redirect('contracts:public')
            except:
                messages.error(request, "You do not have permission to view this contract.")
                return redirect('contracts:public')
        else:
            messages.error(request, "You do not have permission to view this contract.")
            return redirect('contracts:public')
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class ContractUpdateView(LoginRequiredMixin, OwnerOrSecondPartyRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/create_contract.html'

    def get_success_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        self.object = form.save(commit=True, owner=self.request.user)
        messages.success(self.request, "Contract updated.")
        return HttpResponseRedirect(self.get_success_url())

class PublicContractsView(ListView):
    model = Contract
    template_name = 'contracts/public_contracts.html'
    context_object_name = 'contracts'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        qs = Contract.objects.filter(status='ACTIVE') # Only show active contracts
        if user.is_authenticated:
            try:
                profile = user.userprofile
                qs = qs.filter(
                    models.Q(visibility='PUBLIC') |
                    models.Q(visibility='PRIVATE', allowed_companies=profile)
                )
            except UserProfile.DoesNotExist:
                qs = qs.filter(visibility='PUBLIC')
        else:
            qs = qs.filter(visibility='PUBLIC')
        return qs

@login_required
@require_POST
def accept_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    user = request.user

    if user == contract.owner:
        contract.owner_accepted = True
        messages.success(request, "You have accepted the contract as the owner.")
    elif user == contract.second_party:
        contract.second_party_accepted = True
        messages.success(request, "You have accepted the contract as the second party.")
    else:
        messages.error(request, "You are not authorized to accept this contract.")
        return redirect('contracts:detail', pk=pk)

    contract.save() # This will update the status if both are accepted
    return redirect('contracts:detail', pk=pk)

@login_required
@require_POST
def upload_contract_document(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    user = request.user

    # Only allow owner or second_party to upload documents
    if not (user == contract.owner or user == contract.second_party):
        messages.error(request, "You are not authorized to upload documents to this contract.")
        return redirect('contracts:detail', pk=pk)

    # Prevent uploading if contract is already active and both parties have accepted
    if contract.owner_accepted and contract.second_party_accepted and contract.status == 'ACTIVE':
        # Even if active, they can still add, just no deletion
        pass # Allow adding, deletion restriction is in ContractDocument model's delete method

    form = ContractDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            form.save(contract=contract, uploaded_by=user)
            messages.success(request, "Document uploaded successfully.")
        except ValidationError as e:
            messages.error(request, e.message)
        except Exception as e:
            messages.error(request, f"Error uploading document: {e}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('contracts:detail', pk=pk)

def encryption_visualization_view(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    # Ensure only authorized users can view the visualization
    if not (request.user == contract.owner or request.user == contract.second_party or request.user.is_superuser):
        messages.error(request, "You are not authorized to view this visualization.")
        return redirect('contracts:detail', pk=pk)
    return render(request, 'contracts/encryption_visualization.html', {'contract': contract})

@login_required
def view_document(request, contract_pk, doc_pk):
    """Serve file data to the browser without downloads"""
    contract = get_object_or_404(Contract, pk=contract_pk)
    user = request.user

    # Check permission same as ContractDetailView
    if user.is_authenticated:
        if contract.owner == user or contract.second_party == user or user.is_superuser:
            pass
        elif contract.visibility == 'PUBLIC':
            pass
        elif contract.visibility == 'PRIVATE':
            try:
                profile = user.userprofile
                if contract.allowed_companies.filter(pk=profile.pk).exists():
                    pass
                else:
                    messages.error(request, "You do not have permission to view this document.")
                    return redirect('contracts:detail', pk=contract_pk)
            except:
                messages.error(request, "You do not have permission to view this document.")
                return redirect('contracts:detail', pk=contract_pk)
        else:
            messages.error(request, "You do not have permission to view this document.")
            return redirect('contracts:detail', pk=contract_pk)
    else:
        if contract.visibility == 'PUBLIC':
            pass
        else:
            messages.error(request, "You need to log in to view this document.")
            return redirect('accounts:login')

    doc = get_object_or_404(ContractDocument, pk=doc_pk, contract=contract)
    stored = doc.stored_object

    # Read encrypted content
    enc = stored.encrypted_file.read()
    raw = decrypt_bytes(enc)

    # Get file info
    file_name = stored.name
    file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''

    # Content type mapping for common file types
    content_type_mapping = {
        # Images
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'bmp': 'image/bmp', 'svg': 'image/svg+xml',
        'webp': 'image/webp', 'ico': 'image/x-icon',

        # Documents
        'pdf': 'application/pdf',
        'txt': 'text/plain', 'text': 'text/plain',
        'html': 'text/html', 'htm': 'text/html',
        'css': 'text/css', 'js': 'application/javascript',
        'json': 'application/json', 'xml': 'application/xml',

        # Office Documents (browser may not render all, but we try)
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }

    content_type = content_type_mapping.get(file_extension, 'application/octet-stream')

    # Serve file with NO download headers
    response = HttpResponse(raw, content_type=content_type)
    # CRITICAL: No Content-Disposition header prevents downloads
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

@login_required
def universal_viewer(request, contract_pk, doc_pk):
    """Universal file viewer page for all supported file types"""
    contract = get_object_or_404(Contract, pk=contract_pk)
    doc = get_object_or_404(ContractDocument, pk=doc_pk, contract=contract)

    # Check permissions
    user = request.user
    if not (contract.owner == user or contract.second_party == user or
            user.is_superuser or contract.visibility == 'PUBLIC' or
            (contract.visibility == 'PRIVATE' and hasattr(user, 'userprofile') and
             contract.allowed_companies.filter(pk=user.userprofile.pk).exists())):
        messages.error(request, "You do not have permission to view this document.")
        return redirect('contracts:detail', pk=contract_pk)
    
    # Generate absolute URL for the document
    document_url = request.build_absolute_uri(
        reverse('contracts:view_document', kwargs={'contract_pk': contract_pk, 'doc_pk': doc_pk})
    )

    return render(request, 'contracts/universal_viewer.html', {
        'contract': contract,
        'document': doc,
        'document_url': document_url
    })

@login_required
def download_document(request, contract_pk, doc_pk):
    """Serve file data for download"""
    contract = get_object_or_404(Contract, pk=contract_pk)
    user = request.user

    # Check permission same as ContractDetailView
    if user.is_authenticated:
        if contract.owner == user or contract.second_party == user or user.is_superuser:
            pass
        elif contract.visibility == 'PUBLIC':
            pass
        elif contract.visibility == 'PRIVATE':
            try:
                profile = user.userprofile
                if contract.allowed_companies.filter(pk=profile.pk).exists():
                    pass
                else:
                    messages.error(request, "You do not have permission to download this document.")
                    return redirect('contracts:detail', pk=contract_pk)
            except:
                messages.error(request, "You do not have permission to download this document.")
                return redirect('contracts:detail', pk=contract_pk)
        else:
            messages.error(request, "You do not have permission to download this document.")
            return redirect('contracts:detail', pk=contract_pk)
    else:
        if contract.visibility == 'PUBLIC':
            pass
        else:
            messages.error(request, "You need to log in to download this document.")
            return redirect('accounts:login')

    doc = get_object_or_404(ContractDocument, pk=doc_pk, contract=contract)
    stored = doc.stored_object

    # Read encrypted content
    enc = stored.encrypted_file.read()
    raw = decrypt_bytes(enc)

    # Get file info
    file_name = stored.name
    content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

    # Serve file with download headers
    response = HttpResponse(raw, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response
