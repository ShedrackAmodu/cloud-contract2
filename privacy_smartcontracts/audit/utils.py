from .models import AuditEvent

def log_event(event_type: str, user, details: dict):
    try:
        AuditEvent.objects.create(event_type=event_type, user=user if user and hasattr(user, 'pk') else None, details=details or {})
    except Exception:
        # keep audit writes best-effort (shouldn't break main flows)
        pass
