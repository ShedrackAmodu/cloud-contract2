from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DataAccessRequest
from .forms import DataAccessRequestForm
from contracts.models import Contract
from django.contrib import messages
from audit.utils import log_event
from django.utils import timezone

@login_required
def create_request(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if request.method == 'POST':
        form = DataAccessRequestForm(request.POST)
        if form.is_valid():
            dar = form.save(commit=False)
            dar.contract = contract
            dar.requester = request.user
            dar.save()
            log_event('request_created', request.user, {'request_id': dar.id, 'contract_id': contract.id})
            messages.success(request, "Request created.")
            return redirect('requests_app:my_requests')
    else:
        form = DataAccessRequestForm()
    return render(request, 'requests_app/create_request.html', {'form': form, 'contract': contract})

@login_required
def my_requests(request):
    qs = DataAccessRequest.objects.filter(requester=request.user).order_by('-created_at')
    return render(request, 'requests_app/my_requests.html', {'requests': qs})

@login_required
def contract_requests_for_owner(request):
    # owner sees requests for their contracts
    qs = DataAccessRequest.objects.filter(contract__owner=request.user).order_by('-created_at')
    return render(request, 'requests_app/owner_requests.html', {'requests': qs})

@login_required
def process_request(request, request_id, action):
    dar = get_object_or_404(DataAccessRequest, pk=request_id)
    # only contract owner or superuser may approve/deny
    if not (request.user == dar.contract.owner or request.user.is_superuser):
        messages.error(request, "Not allowed")
        return redirect('requests_app:owner_requests')
    if action == 'approve':
        dar.status = 'APPROVED'
    elif action == 'deny':
        dar.status = 'DENIED'
    dar.processed_at = timezone.now()
    dar.save()
    log_event('request_processed', request.user, {'request_id': dar.id, 'action': action})
    messages.success(request, f"Request {action}d.")
    return redirect('requests_app:owner_requests')
