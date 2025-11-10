from django.db import models
from django.conf import settings

class Contract(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
    )
    VISIBILITY_CHOICES = (
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
    )

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contracts')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # policy field: free-form JSON to store policy rules or references
    policy = models.JSONField(default=dict, blank=True)
    # optional file attached to this contract (use MEDIA_ROOT)
    stored_object = models.ForeignKey('storage.StoredObject', on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')

    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    allowed_companies = models.ManyToManyField('users.UserProfile', blank=True, related_name='allowed_contracts', help_text="Companies allowed to view this private contract")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.title} ({self.owner})"
