from django.contrib import admin
from .models import Contract, ContractDocument

class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 0 # No extra empty forms

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','title','owner','second_party', 'owner_accepted', 'second_party_accepted', 'status','created_at')
    list_filter = ('status','created_at','owner','owner_accepted', 'second_party_accepted')
    search_fields = ('title','owner__email', 'second_party__email')
    inlines = [ContractDocumentInline]

@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'stored_object', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('contract__title', 'stored_object__file_name', 'uploaded_by__email')
