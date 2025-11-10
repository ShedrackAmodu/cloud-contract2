from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.CharField(max_length=255, blank=True, help_text="Company represented by the user")

    def __str__(self):
        return f"{self.user.username} - {self.company}"
