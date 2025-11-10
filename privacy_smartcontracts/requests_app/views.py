from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DataAccessRequest
from .forms import DataAccessRequestForm
from contracts.models import Contract
from django.contrib import messages
from audit.utils import log_event
from django.utils import timezone
from oracle.models import Attestation
from oracle.views import load_private_key
from secure_computation.models import SecureComputationValidation
import json, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

@login_required
def create_request(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if not contract.stored_object:
        messages.error(request, "This contract does not have a data file to request access to.")
        return redirect('contracts:public')
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
    # only contract owner or superuser may approve/deny/revoke
    if not (request.user == dar.contract.owner or request.user.is_superuser):
        messages.error(request, "Not allowed")
        return redirect('requests_app:owner_requests')
    if action == 'approve':
        # Perform secure computation validation before approval
        secure_validation, created = SecureComputationValidation.objects.get_or_create(request=dar)
        if not secure_validation.overall_verified:
            validation_success = secure_validation.perform_validation()
            if not validation_success:
                messages.error(request, "Secure computation validation failed. Request cannot be approved.")
                return redirect('requests_app:owner_requests')

        dar.status = 'APPROVED'
        # Auto-attest for PoC
        payload = {"request_id": dar.id, "contract_id": dar.contract.id, "requester": dar.requester.email, "approved_by_oracle": True}
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        priv = load_private_key()
        if priv:
            signature = priv.sign(payload_bytes)
            sig_b64 = base64.b64encode(signature).decode()
            att = Attestation.objects.create(data_request=dar, signer=request.user, payload=payload, signature_b64=sig_b64)
            log_event('attestation_issued', request.user, {'attestation_id': att.id, 'request_id': dar.id})
            messages.success(request, f"Request approved with secure computation validation and attested (id={att.id}).")
        else:
            messages.warning(request, "Request approved but oracle key not configured for auto-attestation.")
    elif action in ['deny', 'revoke']:
        dar.status = 'DENIED'
    dar.processed_at = timezone.now()
    dar.save()
    log_event('request_processed', request.user, {'request_id': dar.id, 'action': action})
    if action != 'approve':
        messages.success(request, f"Request {action}d.")
    return redirect('requests_app:owner_requests')
