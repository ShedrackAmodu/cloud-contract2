from django.db import models
from django.conf import settings
from contracts.models import Contract
from django.db.models.signals import post_save
from django.dispatch import receiver
from oracle.models import Attestation
import json, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from audit.utils import log_event

def load_private_key():
    from django.conf import settings
    b64 = getattr(settings, 'ORACLE_PRIVATE_KEY', None)
    if not b64:
        return None
    raw = base64.b64decode(b64)
    return Ed25519PrivateKey.from_private_bytes(raw)

class DataAccessRequest(models.Model):
    STATUS_CHOICES = (('PENDING','Pending'),('APPROVED','Approved'),('DENIED','Denied'))
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='access_requests')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request {self.id} for {self.contract} by {self.requester}"

@receiver(post_save, sender=DataAccessRequest)
def auto_attest_on_approval(sender, instance, **kwargs):
    if instance.status == 'APPROVED' and not instance.attestations.exists():
        # Auto-attest for approved requests (webhook simulation)
        payload = {"request_id": instance.id, "contract_id": instance.contract.id, "requester": instance.requester.email, "approved_by_oracle": True}
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        priv = load_private_key()
        if priv:
            signature = priv.sign(payload_bytes)
            sig_b64 = base64.b64encode(signature).decode()
            # Create attestation as system (no signer user)
            Attestation.objects.create(data_request=instance, signer=None, payload=payload, signature_b64=sig_b64)
            log_event('auto_attestation_issued', None, {'request_id': instance.id})
