from django.http import HttpResponse
from django.shortcuts import render
from .models import AuditEvent
import csv
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def export_csv(request):
    qs = AuditEvent.objects.order_by('-timestamp').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_events.csv"'
    writer = csv.writer(response)
    writer.writerow(['id','event_type','user','details','timestamp'])
    for a in qs:
        writer.writerow([a.id, a.event_type, getattr(a.user, 'email', ''), a.details, a.timestamp.isoformat()])
    return response

@staff_member_required
def audit_list(request):
    qs = AuditEvent.objects.order_by('-timestamp').all()
    return render(request, 'audit/audit_list.html', {'events': qs})
