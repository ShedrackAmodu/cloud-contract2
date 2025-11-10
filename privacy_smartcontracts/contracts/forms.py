from django import forms
from .models import Contract
import json
from storage.utils import save_encrypted_file

class ContractForm(forms.ModelForm):
    # Policy fields
    purpose = forms.CharField(max_length=255, required=False, help_text="e.g., research, analytics")
    retention_days = forms.IntegerField(required=False, help_text="Number of days to retain data")
    allowed_users = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Comma-separated list of allowed user emails")
    conditions = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Additional conditions")

    allowed_companies = forms.ModelMultipleChoiceField(queryset=None, required=False, widget=forms.SelectMultiple, help_text="Select companies allowed to view this private contract")

    attachment_file = forms.FileField(required=False, label="Data File", help_text="Upload the data file to be shared (will be encrypted automatically). Required for new contracts.")

    class Meta:
        model = Contract
        fields = ("title","description","visibility","status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import UserProfile
        self.fields['allowed_companies'].queryset = UserProfile.objects.all()
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

    def clean(self):
        cleaned_data = super().clean()
        attachment_file = cleaned_data.get('attachment_file')
        instance = getattr(self, 'instance', None)

        # Require file for new contracts
        if not instance or not instance.pk:
            if not attachment_file:
                raise forms.ValidationError("A data file must be uploaded when creating a new contract.")

        return cleaned_data

    def save(self, commit=True, owner=None, files=None):
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

        # handle file: files should be request.FILES or None
        uploaded = None
        if files:
            uploaded = files.get("attachment_file")
        if uploaded and owner:
            stored = save_encrypted_file(owner, uploaded, name=uploaded.name, meta={})
            instance.stored_object = stored

        if owner and not instance.pk:
            instance.owner = owner

        if commit:
            instance.save()
            self.save_m2m()
        return instance
