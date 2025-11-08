from django.contrib import admin
from .models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','title','owner','status','created_at')
    list_filter = ('status','created_at','owner')
    search_fields = ('title','owner__email')
