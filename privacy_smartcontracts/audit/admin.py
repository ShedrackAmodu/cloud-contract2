from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('id','event_type','user','timestamp')
    list_filter = ('event_type','timestamp')
    search_fields = ('user__email','event_type')
