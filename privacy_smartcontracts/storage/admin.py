from django.contrib import admin
from .models import StoredObject

@admin.register(StoredObject)
class StoredObjectAdmin(admin.ModelAdmin):
    list_display = ('id','name','owner','created_at')
    search_fields = ('name','owner__email')
