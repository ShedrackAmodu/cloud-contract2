from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import SecureComputationValidation, TEEGateway
from requests_app.models import DataAccessRequest
import json

@login_required
def tee_dashboard(request):
    """Dashboard showing TEE attestation and cryptographic verification details"""
    from contracts.models import Contract

    # Get user's contracts for filtering
    user_contracts = Contract.objects.filter(owner=request.user)
    contract_filter = request.GET.get('contract')

    # Filter validations based on user permissions and contract selection
    if contract_filter:
        # Show validations for specific contract (if user owns it)
        try:
            selected_contract = Contract.objects.get(id=contract_filter, owner=request.user)
            validations = SecureComputationValidation.objects.filter(
                request__contract=selected_contract
            ).order_by('-created_at')[:20]
        except Contract.DoesNotExist:
            validations = SecureComputationValidation.objects.none()
    else:
        # Show validations for user's contracts OR user's requests
        validations = SecureComputationValidation.objects.filter(
            models.Q(request__contract__owner=request.user) |  # Contracts owned by user
            models.Q(request__requester=request.user)          # Requests made by user
        ).distinct().order_by('-created_at')[:20]

    # Create TEE instance to show capabilities
    tee_instance = TEEGateway()
    request_data = {
        'request_id': 'example-123',
        'contract_id': 'example-contract-456',
        'requester_id': 'example-user-789',
        'contract_owner_id': 'example-owner-101'
    }

    # Perform computation and attestation
    computation = tee_instance.perform_secure_computation(request_data)
    attestation = tee_instance.generate_attestation(computation)

    context = {
        'validations': validations,
        'user_contracts': user_contracts,
        'selected_contract': contract_filter,
        'demo_tee': {
            'enclave_id': tee_instance.enclave_id,
            'measurement': tee_instance.measurement,
            'computation': computation,
            'attestation': attestation
        },
        'page_title': 'TEE Security Dashboard'
    }

    return render(request, 'secure_computation/tee_dashboard.html', context)

@login_required
def tee_validation_detail(request, validation_id):
    """Detailed view of a specific TEE validation"""
    validation = get_object_or_404(SecureComputationValidation, pk=validation_id)

    # Check permissions - user must own the contract or made the request
    if not (
        validation.request.contract.owner == request.user or
        validation.request.requester == request.user
    ):
        from django.http import Http404
        raise Http404("Validation not found or access denied")

    # Verify attestation if present
    attestation_valid = False
    if validation.tee_attestation and 'signature' in validation.tee_attestation:
        try:
            tee_gateway = TEEGateway()
            attestation_valid = tee_gateway.verify_attestation(validation.tee_attestation)
        except:
            attestation_valid = False

    context = {
        'validation': validation,
        'attestation_valid': attestation_valid,
        'zkp_proof': json.dumps(validation.zkp_proof, indent=2) if validation.zkp_proof else None,
        'tee_attestation': json.dumps(validation.tee_attestation, indent=2) if validation.tee_attestation else None,
        'smpc_result': json.dumps(validation.smpc_result, indent=2) if validation.smpc_result else None,
        'page_title': f'TEE Validation #{validation_id}'
    }

    return render(request, 'secure_computation/validation_detail.html', context)
