from django.db import models
from django.conf import settings
from contracts.models import Contract

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
