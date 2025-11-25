from django.db import models
from django.conf import settings

class Attestation(models.Model):
    id = models.AutoField(primary_key=True)
    data_request = models.ForeignKey('requests_app.DataAccessRequest', on_delete=models.CASCADE, related_name='attestations')
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='signed_attestations')
    payload = models.JSONField()
    signature_b64 = models.TextField()  # base64 encoded signature
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attestation {self.id} for request {self.data_request.id}"
