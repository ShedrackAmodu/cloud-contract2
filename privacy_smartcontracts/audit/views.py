from django.http import HttpResponse
from django.shortcuts import render
from .models import AuditEvent
from contracts.models import Contract
from requests_app.models import DataAccessRequest
from secure_computation.models import SecureComputationValidation
from oracle.models import Attestation
import csv
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

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
    """Enhanced audit list showing all system transactions for admin"""
    qs = AuditEvent.objects.order_by('-timestamp').all()
    
    # Filtering options
    event_type_filter = request.GET.get('event_type', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if event_type_filter:
        qs = qs.filter(event_type__icontains=event_type_filter)
    if user_filter:
        qs = qs.filter(user__email__icontains=user_filter)
    if date_from:
        try:
            qs = qs.filter(timestamp__gte=date_from)
        except:
            pass
    if date_to:
        try:
            qs = qs.filter(timestamp__lte=date_to)
        except:
            pass
    
    # Statistics
    total_events = AuditEvent.objects.count()
    events_today = AuditEvent.objects.filter(timestamp__date=timezone.now().date()).count()
    events_this_week = AuditEvent.objects.filter(timestamp__gte=timezone.now() - timedelta(days=7)).count()
    
    # Event type breakdown
    event_types = AuditEvent.objects.values('event_type').annotate(count=Count('id')).order_by('-count')[:10]
    
    context = {
        'events': qs[:500],  # Limit to 500 most recent
        'total_events': total_events,
        'events_today': events_today,
        'events_this_week': events_this_week,
        'event_types': event_types,
        'event_type_filter': event_type_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'audit/audit_list.html', context)

@staff_member_required
def admin_dashboard(request):
    """Comprehensive admin dashboard showing all system transactions and statistics"""
    
    # Contracts Statistics
    total_contracts = Contract.objects.count()
    active_contracts = Contract.objects.filter(status='ACTIVE').count()
    draft_contracts = Contract.objects.filter(status='DRAFT').count()
    pending_contracts = Contract.objects.filter(status='PENDING_CONFIRMATION').count()
    
    # Access Requests Statistics
    total_requests = DataAccessRequest.objects.count()
    pending_requests = DataAccessRequest.objects.filter(status='PENDING').count()
    approved_requests = DataAccessRequest.objects.filter(status='APPROVED').count()
    denied_requests = DataAccessRequest.objects.filter(status='DENIED').count()
    
    # Secure Computation Statistics
    total_validations = SecureComputationValidation.objects.count()
    zkp_verified = SecureComputationValidation.objects.filter(zkp_verified=True).count()
    tee_verified = SecureComputationValidation.objects.filter(tee_verified=True).count()
    smpc_verified = SecureComputationValidation.objects.filter(smpc_verified=True).count()
    overall_verified = SecureComputationValidation.objects.filter(overall_verified=True).count()
    
    # Attestation Statistics
    total_attestations = Attestation.objects.count()
    recent_attestations = Attestation.objects.order_by('-created_at')[:10]
    
    # Audit Statistics
    total_audit_events = AuditEvent.objects.count()
    events_today = AuditEvent.objects.filter(timestamp__date=timezone.now().date()).count()
    
    # Recent Activity
    recent_contracts = Contract.objects.order_by('-created_at')[:10]
    recent_requests = DataAccessRequest.objects.order_by('-created_at')[:10]
    recent_validations = SecureComputationValidation.objects.order_by('-created_at')[:10]
    recent_audit_events = AuditEvent.objects.order_by('-timestamp')[:20]
    
    # Security Layer Breakdown
    security_stats = {
        'zkp_success_rate': (zkp_verified / total_validations * 100) if total_validations > 0 else 0,
        'tee_success_rate': (tee_verified / total_validations * 100) if total_validations > 0 else 0,
        'smpc_success_rate': (smpc_verified / total_validations * 100) if total_validations > 0 else 0,
        'overall_success_rate': (overall_verified / total_validations * 100) if total_validations > 0 else 0,
    }
    
    context = {
        # Contracts
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'draft_contracts': draft_contracts,
        'pending_contracts': pending_contracts,
        'recent_contracts': recent_contracts,
        
        # Requests
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'denied_requests': denied_requests,
        'recent_requests': recent_requests,
        
        # Secure Computation
        'total_validations': total_validations,
        'zkp_verified': zkp_verified,
        'tee_verified': tee_verified,
        'smpc_verified': smpc_verified,
        'overall_verified': overall_verified,
        'recent_validations': recent_validations,
        'security_stats': security_stats,
        
        # Attestations
        'total_attestations': total_attestations,
        'recent_attestations': recent_attestations,
        
        # Audit
        'total_audit_events': total_audit_events,
        'events_today': events_today,
        'recent_audit_events': recent_audit_events,
    }
    
    return render(request, 'audit/admin_dashboard.html', context)
