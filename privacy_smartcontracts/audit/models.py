from django.db import models
from django.conf import settings

class AuditEvent(models.Model):
    id = models.AutoField(primary_key=True)
    event_type = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} by {self.user} at {self.timestamp}"
