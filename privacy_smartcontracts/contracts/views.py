from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from .models import Contract
from .forms import ContractForm
from django.contrib import messages
from django.http import HttpResponseRedirect

class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = getattr(self, 'object', None)
        if obj is None:
            # For create/list views, check user is authenticated
            return self.request.user.is_authenticated
        return obj.owner == self.request.user or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to view that.")
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
        return Contract.objects.filter(owner=user)

class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/create_contract.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Contract created.")
        return resp

    def get_success_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})

class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/view_contract.html'
    context_object_name = 'contract'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # restrict access: owner or admin or other business rule
        if self.object.owner != request.user and not request.user.is_superuser:
            messages.error(request, "You do not have permission to view this contract.")
            return redirect('contracts:dashboard')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class ContractUpdateView(LoginRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/create_contract.html'

    def dispatch(self, request, *args, **kwargs):
        # ensure only owner or superuser can update
        self.object = self.get_object()
        if self.object.owner != request.user and not request.user.is_superuser:
            messages.error(request, "You do not have permission to edit this contract.")
            return redirect('contracts:dashboard')
        return super().dispatch(request, *args, **kwargs)


    def get_success_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # pass request.FILES into form via attribute so form.save can access
        form.files = self.request.FILES
        self.object = form.save(commit=True, owner=self.request.user)
        messages.success(self.request, "Contract created.")
        return HttpResponseRedirect(self.get_success_url())
