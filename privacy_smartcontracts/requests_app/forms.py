from django import forms
from .models import DataAccessRequest

class DataAccessRequestForm(forms.ModelForm):
    class Meta:
        model = DataAccessRequest
        fields = ('reason',)
