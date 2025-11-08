from django.db import models
from django.conf import settings

def upload_path(instance, filename):
    return f"encrypted/{instance.owner.id}/{filename}.enc"

class StoredObject(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stored_objects")
    name = models.CharField(max_length=255)
    encrypted_file = models.FileField(upload_to=upload_path)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"
