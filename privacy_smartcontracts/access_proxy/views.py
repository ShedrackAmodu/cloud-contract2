from django.shortcuts import get_object_or_404, redirect
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
        return HttpResponse("Not authorized", status=403)

    # find attestation
    att = Attestation.objects.filter(data_request=dar).order_by('-issued_at').first()
    if not att:
        return HttpResponse("Attestation not found", status=404)

    # verify signature
    pub = load_public_key()
    if not pub:
        return HttpResponse("Server misconfigured: ORACLE_PUBLIC_KEY missing", status=500)

    payload_bytes = json.dumps(att.payload, sort_keys=True).encode()
    try:
        pub.verify(base64.b64decode(att.signature_b64), payload_bytes)
    except Exception:
        return HttpResponse("Invalid attestation signature", status=403)

    # ensure request APPROVED
    if dar.status != 'APPROVED':
        return HttpResponse("Request not approved", status=403)

    # get stored object
    stored = dar.contract.stored_object
    if not stored:
        return HttpResponse("No stored object available", status=404)

    enc = stored.encrypted_file.read()
    raw = decrypt_bytes(enc)
    log_event('access_granted', request.user, {'request_id': dar.id, 'object_id': stored.id, 'attestation_id': att.id})
    resp = HttpResponse(raw, content_type='application/octet-stream')
    resp['Content-Disposition'] = f'attachment; filename="{stored.name}"'
    return resp
