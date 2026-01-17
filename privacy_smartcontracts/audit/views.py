from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .models import AuditEvent
from contracts.models import Contract
from requests_app.models import DataAccessRequest
from secure_computation.models import SecureComputationValidation
from oracle.models import Attestation
import csv
import json
import os
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime, date
from pathlib import Path
import sys

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
    recent_attestations = Attestation.objects.order_by('-issued_at')[:10]
    
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

@staff_member_required
def fitness_margin_report(request):
    """Generate fitness margin improvements report with graphs"""
    # Import fitness margin calculator
    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(BASE_DIR))
    from fitness_margin_calculator import FitnessMarginCalculator
    
    calculator = FitnessMarginCalculator()
    
    # Check if baseline file exists
    baseline_file = request.GET.get('baseline', None)
    baseline_data = None
    
    if baseline_file and os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
    
    # Calculate metrics
    results = calculator.calculate_fitness_margins(baseline_data)
    
    # Prepare data for graphs
    graph_data = prepare_graph_data(results)
    
    # Serialize results for JavaScript (handle datetime and other non-serializable types)
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    context = {
        'results': results,
        'results_json': json.dumps(results, default=json_serial),  # For saveAsBaseline function
        'graph_data': json.dumps(graph_data, default=json_serial),  # Serialize to JSON for JavaScript
        'has_baseline': baseline_data is not None,
        'baseline_file': baseline_file,
    }
    
    return render(request, 'audit/fitness_margin_report.html', context)

def prepare_graph_data(results):
    """Prepare data in format suitable for Chart.js"""
    graph_data = {
        'request_processing': {},
        'security_validation': {},
        'system_throughput': {},
        'attestation_efficiency': {}
    }
    
    if 'improvements' in results:
        # Request Processing
        rp = results['improvements']['request_processing']
        graph_data['request_processing'] = {
            'approval_rate': {
                'baseline': results['baseline']['request_processing'].get('approval_rate', 0),
                'current': results['current']['request_processing'].get('approval_rate', 0),
                'improvement': rp.get('approval_rate_improvement', 0)
            },
            'processing_time': {
                'baseline': results['baseline']['request_processing'].get('avg_processing_time_hours', 0) or 0,
                'current': results['current']['request_processing'].get('avg_processing_time_hours', 0) or 0,
                'reduction': rp.get('processing_time_reduction', 0) or 0
            }
        }
        
        # Security Validation
        sv = results['improvements']['security_validation']
        graph_data['security_validation'] = {
            'zkp': {
                'baseline': results['baseline']['security_validation'].get('zkp_success_rate', 0),
                'current': results['current']['security_validation'].get('zkp_success_rate', 0),
                'improvement': sv.get('zkp_success_rate_improvement', 0)
            },
            'tee': {
                'baseline': results['baseline']['security_validation'].get('tee_success_rate', 0),
                'current': results['current']['security_validation'].get('tee_success_rate', 0),
                'improvement': sv.get('tee_success_rate_improvement', 0)
            },
            'smpc': {
                'baseline': results['baseline']['security_validation'].get('smpc_success_rate', 0),
                'current': results['current']['security_validation'].get('smpc_success_rate', 0),
                'improvement': sv.get('smpc_success_rate_improvement', 0)
            },
            'overall': {
                'baseline': results['baseline']['security_validation'].get('overall_success_rate', 0),
                'current': results['current']['security_validation'].get('overall_success_rate', 0),
                'improvement': sv.get('overall_success_rate_improvement', 0)
            }
        }
        
        # System Throughput
        st = results['improvements']['system_throughput']
        graph_data['system_throughput'] = {
            'contracts_per_day': {
                'baseline': results['baseline']['system_throughput'].get('contracts_per_day', 0),
                'current': results['current']['system_throughput'].get('contracts_per_day', 0),
                'improvement': st.get('contracts_per_day_improvement', 0)
            },
            'requests_per_day': {
                'baseline': results['baseline']['system_throughput'].get('requests_per_day', 0),
                'current': results['current']['system_throughput'].get('requests_per_day', 0),
                'improvement': st.get('requests_per_day_improvement', 0)
            }
        }
        
        # Attestation Efficiency
        ae = results['improvements']['attestation_efficiency']
        graph_data['attestation_efficiency'] = {
            'attestation_rate': {
                'baseline': results['baseline']['attestation_efficiency'].get('attestation_rate', 0),
                'current': results['current']['attestation_efficiency'].get('attestation_rate', 0),
                'improvement': ae.get('attestation_rate_improvement', 0)
            },
            'attestation_time': {
                'baseline': results['baseline']['attestation_efficiency'].get('avg_attestation_time_minutes', 0) or 0,
                'current': results['current']['attestation_efficiency'].get('avg_attestation_time_minutes', 0) or 0,
                'reduction': ae.get('attestation_time_reduction', 0) or 0
            }
        }
    else:
        # Current metrics only (no baseline)
        current = results
        graph_data['request_processing'] = {
            'approval_rate': current['request_processing'].get('approval_rate', 0),
            'processing_time': current['request_processing'].get('avg_processing_time_hours', 0) or 0
        }
        graph_data['security_validation'] = {
            'zkp': current['security_validation'].get('zkp_success_rate', 0),
            'tee': current['security_validation'].get('tee_success_rate', 0),
            'smpc': current['security_validation'].get('smpc_success_rate', 0),
            'overall': current['security_validation'].get('overall_success_rate', 0)
        }
        graph_data['system_throughput'] = {
            'contracts_per_day': current['system_throughput'].get('contracts_per_day', 0),
            'requests_per_day': current['system_throughput'].get('requests_per_day', 0)
        }
        graph_data['attestation_efficiency'] = {
            'attestation_rate': current['attestation_efficiency'].get('attestation_rate', 0),
            'attestation_time': current['attestation_efficiency'].get('avg_attestation_time_minutes', 0) or 0
        }
    
    return graph_data
