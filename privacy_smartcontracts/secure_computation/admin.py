from django.contrib import admin
from .models import SecureComputationValidation

@admin.register(SecureComputationValidation)
class SecureComputationValidationAdmin(admin.ModelAdmin):
    list_display = ('request', 'zkp_verified', 'tee_verified', 'smpc_verified', 'overall_verified', 'created_at', 'validated_at')
    list_filter = ('zkp_verified', 'tee_verified', 'smpc_verified', 'overall_verified', 'created_at', 'validated_at')
    readonly_fields = ('zkp_proof', 'tee_attestation', 'smpc_result', 'created_at', 'validated_at')
    search_fields = ('request__id', 'request__contract__title', 'request__requester__email')
