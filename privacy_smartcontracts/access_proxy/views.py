from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from oracle.models import Attestation
from requests_app.models import DataAccessRequest
from storage.utils import decrypt_bytes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import base64, json
from audit.utils import log_event

def load_public_key():
    b64 = getattr(settings, 'ORACLE_PUBLIC_KEY', None)
    if not b64:
        return None
    raw = base64.b64decode(b64)
    return Ed25519PublicKey.from_public_bytes(raw)

@login_required
def retrieve(request, data_request_id):
    """
    Retrieve endpoint for requester to click. Will look up the latest attestation for the data_request_id,
    verify signature using ORACLE_PUBLIC_KEY and then decrypt & send the stored object attached to the contract.
    """
    dar = get_object_or_404(DataAccessRequest, pk=data_request_id)
    # ensure requester matches the user (only requester can retrieve)
    if request.user != dar.requester and not request.user.is_superuser:
        return render(request, 'access_proxy/error.html', {'error': 'Not authorized'})

    # find attestation
    att = Attestation.objects.filter(data_request=dar).order_by('-issued_at').first()
    if not att:
        return render(request, 'access_proxy/error.html', {'error': 'Attestation not found'})

    # verify signature
    pub = load_public_key()
    if not pub:
        return render(request, 'access_proxy/error.html', {'error': 'Server misconfigured: ORACLE_PUBLIC_KEY missing'})

    payload_bytes = json.dumps(att.payload, sort_keys=True).encode()
    try:
        pub.verify(base64.b64decode(att.signature_b64), payload_bytes)
    except Exception:
        return render(request, 'access_proxy/error.html', {'error': 'Invalid attestation signature'})

    # ensure request APPROVED
    if dar.status != 'APPROVED':
        return render(request, 'access_proxy/error.html', {'error': 'Request not approved'})

    # get stored object
    stored = dar.contract.stored_object
    if not stored:
        return render(request, 'access_proxy/error.html', {'error': 'No stored object available'})

    enc = stored.encrypted_file.read()
    raw = decrypt_bytes(enc)
    log_event('access_granted', request.user, {'request_id': dar.id, 'object_id': stored.id, 'attestation_id': att.id})
    resp = HttpResponse(raw, content_type='application/octet-stream')
    resp['Content-Disposition'] = f'attachment; filename="{stored.name}"'
    return resp
