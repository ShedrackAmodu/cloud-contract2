from django import forms
from .models import Contract
import json
from storage.utils import save_encrypted_file

class ContractForm(forms.ModelForm):
    policy_json = forms.CharField(widget=forms.Textarea(attrs={"rows":6}), required=False)
    attachment_file = forms.FileField(required=False)

    class Meta:
        model = Contract
        fields = ("title","description","status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate policy_json when editing
        instance = kwargs.get("instance")
        if instance and instance.policy:
            self.initial["policy_json"] = json.dumps(instance.policy, indent=2)

    def clean_policy_json(self):
        raw = self.cleaned_data.get("policy_json","") or ""
        raw = raw.strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception as e:
            raise forms.ValidationError(f"Invalid JSON: {e}")

    def save(self, commit=True, owner=None, files=None):
        instance = super().save(commit=False)
        instance.policy = self.cleaned_data.get("policy_json", {}) or {}

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
