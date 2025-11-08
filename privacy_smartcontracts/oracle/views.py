from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from requests_app.models import DataAccessRequest
from .models import Attestation
from django.contrib import messages
from django.conf import settings
import json, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from audit.utils import log_event

def load_private_key():
    b64 = getattr(settings, 'ORACLE_PRIVATE_KEY', None)
    if not b64:
        return None
    raw = base64.b64decode(b64)
    return Ed25519PrivateKey.from_private_bytes(raw)

@login_required
def list_pending_for_oracle(request):
    # simple listing of approved requests (signed only after approval)
    qs = DataAccessRequest.objects.filter(status='APPROVED').order_by('-processed_at')[:50]
    return render(request, 'oracle/pending_list.html', {'requests': qs})

@login_required
def sign_request(request, request_id):
    dar = get_object_or_404(DataAccessRequest, pk=request_id)
    # Only allow signing if APPROVED
    if dar.status != 'APPROVED':
        messages.error(request, "Request is not approved.")
        return redirect('oracle:pending')
    if request.method == 'POST':
        # build payload
        payload = {"request_id": dar.id, "contract_id": dar.contract.id, "requester": dar.requester.email, "approved_by_oracle": True}
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        priv = load_private_key()
        if not priv:
            messages.error(request, "Oracle private key not configured.")
            return redirect('oracle:pending')
        signature = priv.sign(payload_bytes)
        sig_b64 = base64.b64encode(signature).decode()
        att = Attestation.objects.create(data_request=dar, signer=request.user, payload=payload, signature_b64=sig_b64)
        log_event('attestation_issued', request.user, {'attestation_id': att.id, 'request_id': dar.id})
        messages.success(request, f"Attestation created (id={att.id})")
        return redirect('oracle:pending')
    return render(request, 'oracle/sign_confirm.html', {'request_obj': dar})
