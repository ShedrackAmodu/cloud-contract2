from django import forms
from .models import Contract, ContractDocument
import json
from storage.utils import save_encrypted_file
from users.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class ContractForm(forms.ModelForm):
    # Policy fields
    purpose = forms.CharField(max_length=255, required=False, help_text="e.g., research, analytics")
    retention_days = forms.IntegerField(required=False, help_text="Number of days to retain data")
    allowed_users = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Comma-separated list of allowed user emails")
    conditions = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Additional conditions")

    allowed_companies = forms.ModelMultipleChoiceField(queryset=UserProfile.objects.all(), required=False, widget=forms.SelectMultiple, help_text="Select companies allowed to view this private contract")
    second_party = forms.ModelChoiceField(queryset=User.objects.all(), required=False, help_text="Select the second party for this contract")

    class Meta:
        model = Contract
        fields = ("title", "description", "visibility", "second_party") # Removed status as it's updated internally

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate policy fields when editing
        instance = kwargs.get("instance")
        if instance and instance.policy:
            policy = instance.policy
            self.initial["purpose"] = policy.get("purpose", "")
            self.initial["retention_days"] = policy.get("retention_days")
            self.initial["allowed_users"] = policy.get("allowed_users", "")
            self.initial["conditions"] = policy.get("conditions", "")
        if instance:
            self.initial['allowed_companies'] = instance.allowed_companies.all()
            if instance.second_party:
                self.initial['second_party'] = instance.second_party

    def save(self, commit=True, owner=None):
        instance = super().save(commit=False)
        
        # build policy dict
        policy = {}
        if self.cleaned_data.get("purpose"):
            policy["purpose"] = self.cleaned_data["purpose"]
        if self.cleaned_data.get("retention_days"):
            policy["retention_days"] = self.cleaned_data["retention_days"]
        if self.cleaned_data.get("allowed_users"):
            policy["allowed_users"] = self.cleaned_data["allowed_users"]
        if self.cleaned_data.get("conditions"):
            policy["conditions"] = self.cleaned_data["conditions"]
        instance.policy = policy

        if owner and not instance.pk:
            instance.owner = owner

        if commit:
            instance.save()
            self.save_m2m() # Save ManyToMany relationships like allowed_companies
        return instance

class ContractDocumentForm(forms.ModelForm):
    attachment_file = forms.FileField(required=True, label="Upload Document", help_text="Upload a new document for this contract (will be encrypted automatically).")

    class Meta:
        model = ContractDocument
        fields = ('attachment_file',) # Only file upload field

    def save(self, contract, uploaded_by, commit=True):
        uploaded_file = self.cleaned_data['attachment_file']
        stored = save_encrypted_file(uploaded_by, uploaded_file, name=uploaded_file.name, meta={})
        
        contract_document = super().save(commit=False)
        contract_document.contract = contract
        contract_document.stored_object = stored
        contract_document.uploaded_by = uploaded_by

        if commit:
            contract_document.save()
        return contract_document
