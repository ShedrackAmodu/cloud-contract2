"""
Fitness Margin Improvements Calculator
Calculates performance improvements and efficiency gains in the system
by comparing baseline metrics with current system performance.
"""
import json
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from contracts.models import Contract
from requests_app.models import DataAccessRequest
from secure_computation.models import SecureComputationValidation
from oracle.models import Attestation
from audit.models import AuditEvent

class FitnessMarginCalculator:
    """
    Calculates fitness margin improvements by comparing:
    1. Request processing efficiency
    2. Security validation success rates
    3. System throughput
    4. Average processing times
    """
    
    def __init__(self):
        self.results = {}
    
    def calculate_request_processing_efficiency(self):
        """Calculate efficiency of request processing"""
        total_requests = DataAccessRequest.objects.count()
        approved_requests = DataAccessRequest.objects.filter(status='APPROVED').count()
        denied_requests = DataAccessRequest.objects.filter(status='DENIED').count()
        pending_requests = DataAccessRequest.objects.filter(status='PENDING').count()
        
        if total_requests > 0:
            approval_rate = (approved_requests / total_requests) * 100
            processing_rate = ((approved_requests + denied_requests) / total_requests) * 100
        else:
            approval_rate = 0
            processing_rate = 0
        
        # Calculate average processing time (time from creation to processing)
        processed_requests = DataAccessRequest.objects.filter(
            processed_at__isnull=False
        )
        
        avg_processing_time = None
        if processed_requests.exists():
            processing_times = []
            for req in processed_requests:
                if req.processed_at and req.created_at:
                    delta = req.processed_at - req.created_at
                    processing_times.append(delta.total_seconds())
            
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            'total_requests': total_requests,
            'approved_requests': approved_requests,
            'denied_requests': denied_requests,
            'pending_requests': pending_requests,
            'approval_rate': approval_rate,
            'processing_rate': processing_rate,
            'avg_processing_time_seconds': avg_processing_time,
            'avg_processing_time_hours': avg_processing_time / 3600 if avg_processing_time else None
        }
    
    def calculate_security_validation_success_rate(self):
        """Calculate success rates for security validations"""
        total_validations = SecureComputationValidation.objects.count()
        
        if total_validations == 0:
            return {
                'total_validations': 0,
                'zkp_success_rate': 0,
                'tee_success_rate': 0,
                'smpc_success_rate': 0,
                'overall_success_rate': 0
            }
        
        zkp_verified = SecureComputationValidation.objects.filter(zkp_verified=True).count()
        tee_verified = SecureComputationValidation.objects.filter(tee_verified=True).count()
        smpc_verified = SecureComputationValidation.objects.filter(smpc_verified=True).count()
        overall_verified = SecureComputationValidation.objects.filter(overall_verified=True).count()
        
        return {
            'total_validations': total_validations,
            'zkp_verified': zkp_verified,
            'tee_verified': tee_verified,
            'smpc_verified': smpc_verified,
            'overall_verified': overall_verified,
            'zkp_success_rate': (zkp_verified / total_validations) * 100,
            'tee_success_rate': (tee_verified / total_validations) * 100,
            'smpc_success_rate': (smpc_verified / total_validations) * 100,
            'overall_success_rate': (overall_verified / total_validations) * 100
        }
    
    def calculate_system_throughput(self):
        """Calculate system throughput metrics"""
        # Contracts created per day (average)
        total_contracts = Contract.objects.count()
        if total_contracts > 0:
            first_contract = Contract.objects.order_by('created_at').first()
            days_since_start = (timezone.now() - first_contract.created_at).days
            if days_since_start > 0:
                contracts_per_day = total_contracts / days_since_start
            else:
                contracts_per_day = total_contracts
        else:
            contracts_per_day = 0
        
        # Requests processed per day
        total_requests = DataAccessRequest.objects.count()
        if total_requests > 0:
            first_request = DataAccessRequest.objects.order_by('created_at').first()
            days_since_start = (timezone.now() - first_request.created_at).days
            if days_since_start > 0:
                requests_per_day = total_requests / days_since_start
            else:
                requests_per_day = total_requests
        else:
            requests_per_day = 0
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        contracts_this_week = Contract.objects.filter(created_at__gte=week_ago).count()
        requests_this_week = DataAccessRequest.objects.filter(created_at__gte=week_ago).count()
        validations_this_week = SecureComputationValidation.objects.filter(created_at__gte=week_ago).count()
        
        return {
            'contracts_per_day': contracts_per_day,
            'requests_per_day': requests_per_day,
            'contracts_this_week': contracts_this_week,
            'requests_this_week': requests_this_week,
            'validations_this_week': validations_this_week
        }
    
    def calculate_attestation_efficiency(self):
        """Calculate oracle attestation efficiency"""
        total_attestations = Attestation.objects.count()
        total_approved_requests = DataAccessRequest.objects.filter(status='APPROVED').count()
        
        if total_approved_requests > 0:
            attestation_rate = (total_attestations / total_approved_requests) * 100
        else:
            attestation_rate = 0
        
        # Average time from approval to attestation
        attested_requests = DataAccessRequest.objects.filter(
            status='APPROVED',
            attestations__isnull=False
        ).distinct()
        
        avg_attestation_time = None
        if attested_requests.exists():
            attestation_times = []
            for req in attested_requests:
                attestation = req.attestations.first()
                if attestation and req.processed_at:
                    delta = attestation.issued_at - req.processed_at
                    attestation_times.append(delta.total_seconds())
            
            if attestation_times:
                avg_attestation_time = sum(attestation_times) / len(attestation_times)
        
        return {
            'total_attestations': total_attestations,
            'total_approved_requests': total_approved_requests,
            'attestation_rate': attestation_rate,
            'avg_attestation_time_seconds': avg_attestation_time,
            'avg_attestation_time_minutes': avg_attestation_time / 60 if avg_attestation_time else None
        }
    
    def calculate_fitness_margins(self, baseline_data=None):
        """
        Calculate fitness margin improvements
        If baseline_data is provided, compares current metrics to baseline
        Otherwise, returns current metrics as baseline
        """
        current_metrics = {
            'request_processing': self.calculate_request_processing_efficiency(),
            'security_validation': self.calculate_security_validation_success_rate(),
            'system_throughput': self.calculate_system_throughput(),
            'attestation_efficiency': self.calculate_attestation_efficiency(),
            'timestamp': timezone.now().isoformat()
        }
        
        if baseline_data:
            # Calculate improvements
            improvements = {}
            
            # Request Processing Improvements
            rp_current = current_metrics['request_processing']
            rp_baseline = baseline_data.get('request_processing', {})
            
            improvements['request_processing'] = {
                'approval_rate_improvement': rp_current.get('approval_rate', 0) - rp_baseline.get('approval_rate', 0),
                'processing_rate_improvement': rp_current.get('processing_rate', 0) - rp_baseline.get('processing_rate', 0),
                'processing_time_reduction': (rp_baseline.get('avg_processing_time_seconds', 0) - 
                                            rp_current.get('avg_processing_time_seconds', 0)) 
                                            if rp_baseline.get('avg_processing_time_seconds') else None,
                'processing_time_reduction_percent': (
                    ((rp_baseline.get('avg_processing_time_seconds', 0) - 
                      rp_current.get('avg_processing_time_seconds', 0)) / 
                     rp_baseline.get('avg_processing_time_seconds', 1)) * 100
                    if rp_baseline.get('avg_processing_time_seconds') else None
                )
            }
            
            # Security Validation Improvements
            sv_current = current_metrics['security_validation']
            sv_baseline = baseline_data.get('security_validation', {})
            
            improvements['security_validation'] = {
                'zkp_success_rate_improvement': sv_current.get('zkp_success_rate', 0) - sv_baseline.get('zkp_success_rate', 0),
                'tee_success_rate_improvement': sv_current.get('tee_success_rate', 0) - sv_baseline.get('tee_success_rate', 0),
                'smpc_success_rate_improvement': sv_current.get('smpc_success_rate', 0) - sv_baseline.get('smpc_success_rate', 0),
                'overall_success_rate_improvement': sv_current.get('overall_success_rate', 0) - sv_baseline.get('overall_success_rate', 0)
            }
            
            # System Throughput Improvements
            st_current = current_metrics['system_throughput']
            st_baseline = baseline_data.get('system_throughput', {})
            
            improvements['system_throughput'] = {
                'contracts_per_day_improvement': st_current.get('contracts_per_day', 0) - st_baseline.get('contracts_per_day', 0),
                'requests_per_day_improvement': st_current.get('requests_per_day', 0) - st_baseline.get('requests_per_day', 0),
                'contracts_per_day_improvement_percent': (
                    ((st_current.get('contracts_per_day', 0) - st_baseline.get('contracts_per_day', 0)) / 
                     st_baseline.get('contracts_per_day', 1)) * 100
                    if st_baseline.get('contracts_per_day', 0) > 0 else None
                ),
                'requests_per_day_improvement_percent': (
                    ((st_current.get('requests_per_day', 0) - st_baseline.get('requests_per_day', 0)) / 
                     st_baseline.get('requests_per_day', 1)) * 100
                    if st_baseline.get('requests_per_day', 0) > 0 else None
                )
            }
            
            # Attestation Efficiency Improvements
            ae_current = current_metrics['attestation_efficiency']
            ae_baseline = baseline_data.get('attestation_efficiency', {})
            
            improvements['attestation_efficiency'] = {
                'attestation_rate_improvement': ae_current.get('attestation_rate', 0) - ae_baseline.get('attestation_rate', 0),
                'attestation_time_reduction': (ae_baseline.get('avg_attestation_time_seconds', 0) - 
                                              ae_current.get('avg_attestation_time_seconds', 0))
                                              if ae_baseline.get('avg_attestation_time_seconds') else None,
                'attestation_time_reduction_percent': (
                    ((ae_baseline.get('avg_attestation_time_seconds', 0) - 
                      ae_current.get('avg_attestation_time_seconds', 0)) / 
                     ae_baseline.get('avg_attestation_time_seconds', 1)) * 100
                    if ae_baseline.get('avg_attestation_time_seconds') else None
                )
            }
            
            return {
                'baseline': baseline_data,
                'current': current_metrics,
                'improvements': improvements,
                'timestamp': timezone.now().isoformat()
            }
        else:
            return current_metrics
    
    def save_results(self, data, filename='fitness_margin_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Results saved to {filename}")
    
    def generate_report(self, improvements_data):
        """Generate human-readable report"""
        print("\n" + "=" * 80)
        print("FITNESS MARGIN IMPROVEMENTS REPORT")
        print("=" * 80)
        
        if 'improvements' in improvements_data:
            imp = improvements_data['improvements']
            
            print("\n1. REQUEST PROCESSING IMPROVEMENTS")
            print("-" * 80)
            rp = imp['request_processing']
            print(f"   Approval Rate Improvement: {rp['approval_rate_improvement']:.2f}%")
            print(f"   Processing Rate Improvement: {rp['processing_rate_improvement']:.2f}%")
            if rp['processing_time_reduction']:
                print(f"   Processing Time Reduction: {rp['processing_time_reduction']:.2f} seconds ({rp['processing_time_reduction_percent']:.2f}%)")
            
            print("\n2. SECURITY VALIDATION IMPROVEMENTS")
            print("-" * 80)
            sv = imp['security_validation']
            print(f"   ZKP Success Rate Improvement: {sv['zkp_success_rate_improvement']:.2f}%")
            print(f"   TEE Success Rate Improvement: {sv['tee_success_rate_improvement']:.2f}%")
            print(f"   SMPC Success Rate Improvement: {sv['smpc_success_rate_improvement']:.2f}%")
            print(f"   Overall Success Rate Improvement: {sv['overall_success_rate_improvement']:.2f}%")
            
            print("\n3. SYSTEM THROUGHPUT IMPROVEMENTS")
            print("-" * 80)
            st = imp['system_throughput']
            print(f"   Contracts Per Day Improvement: {st['contracts_per_day_improvement']:.2f} ({st['contracts_per_day_improvement_percent']:.2f}%)")
            print(f"   Requests Per Day Improvement: {st['requests_per_day_improvement']:.2f} ({st['requests_per_day_improvement_percent']:.2f}%)")
            
            print("\n4. ATTESTATION EFFICIENCY IMPROVEMENTS")
            print("-" * 80)
            ae = imp['attestation_efficiency']
            print(f"   Attestation Rate Improvement: {ae['attestation_rate_improvement']:.2f}%")
            if ae['attestation_time_reduction']:
                print(f"   Attestation Time Reduction: {ae['attestation_time_reduction']:.2f} seconds ({ae['attestation_time_reduction_percent']:.2f}%)")
        else:
            print("\nCURRENT SYSTEM METRICS (Baseline)")
            print("-" * 80)
            print("\nUse this as baseline for future comparisons.")
        
        print("\n" + "=" * 80)


# Django management command usage
def run_calculation(baseline_file=None):
    """Run fitness margin calculation"""
    import os
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'privacy_smartcontracts.settings')
    django.setup()
    
    calculator = FitnessMarginCalculator()
    
    baseline_data = None
    if baseline_file and os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        print(f"Loaded baseline data from {baseline_file}")
    
    results = calculator.calculate_fitness_margins(baseline_data)
    calculator.save_results(results)
    calculator.generate_report(results)
    
    return results

if __name__ == '__main__':
    import sys
    baseline_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_calculation(baseline_file)

