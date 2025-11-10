from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    company = forms.CharField(max_length=255, required=False, help_text="Company you represent")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            from .models import UserProfile
            UserProfile.objects.create(user=user, company=self.cleaned_data.get('company', ''))
        return user
