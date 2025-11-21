from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Contract(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING_CONFIRMATION', 'Pending Confirmation'),
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
    policy = models.JSONField(default=dict, blank=True)
    
    # New fields for two-sided confirmation
    owner_accepted = models.BooleanField(default=False)
    second_party = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_contracts')
    second_party_accepted = models.BooleanField(default=False)

    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    allowed_companies = models.ManyToManyField('users.UserProfile', blank=True, related_name='allowed_contracts', help_text="Companies allowed to view this private contract")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.title} ({self.owner})"

    def save(self, *args, **kwargs):
        # Update status based on confirmations
        if self.owner_accepted and self.second_party_accepted and self.status == 'PENDING_CONFIRMATION':
            self.status = 'ACTIVE'
        elif (self.owner_accepted or self.second_party_accepted) and self.status == 'DRAFT':
            self.status = 'PENDING_CONFIRMATION'
        super().save(*args, **kwargs)

class ContractDocument(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='documents')
    stored_object = models.ForeignKey('storage.StoredObject', on_delete=models.PROTECT) # Prevent deletion of StoredObject if it's linked to a contract
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contract', 'stored_object') # A document can only be linked once per contract

    def __str__(self):
        return f"Document for {self.contract.title}: {self.stored_object.file_name}"

    def delete(self, *args, **kwargs):
        if self.contract.owner_accepted and self.contract.second_party_accepted:
            raise ValidationError("Cannot remove documents from an accepted contract.")
        super().delete(*args, **kwargs)
