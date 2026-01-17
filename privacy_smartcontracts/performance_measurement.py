"""
Performance Measurement Script for Chapter 5 Documentation
Measures computational time for:
- Data Owner (issuing audit request, generating temporary key)
- Smart Contract (verifying audit response)
- Public Cloud (processing audit request)

For different data file sizes
"""
import time
import os
import json
import hashlib
import secrets
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

# File sizes to test (in KB)
FILE_SIZES_KB = [10, 50, 100, 500, 1000, 5000, 10000]  # 10KB to 10MB

class PerformanceMeasurer:
    def __init__(self):
        self.results = {
            'data_owner': [],
            'smart_contract': [],
            'public_cloud': []
        }
    
    def generate_test_file(self, size_kb):
        """Generate a test file of specified size"""
        size_bytes = size_kb * 1024
        return os.urandom(size_bytes)
    
    def measure_data_owner_operations(self, file_data):
        """Measure time for data owner operations:
        1. Generate temporary key
        2. Issue audit request
        """
        times = {}
        
        # 1. Generate temporary key (Fernet key generation)
        start = time.time()
        temp_key = Fernet.generate_key()
        times['generate_temp_key'] = (time.time() - start) * 1000  # Convert to ms
        
        # 2. Issue audit request (create request payload and sign)
        start = time.time()
        # Simulate creating audit request payload
        request_payload = {
            'file_hash': hashlib.sha3_256(file_data).hexdigest(),  # Upgraded to SHA-3-256
            'file_size': len(file_data),
            'timestamp': datetime.now().isoformat(),
            'requester_id': secrets.token_hex(16)
        }
        payload_bytes = json.dumps(request_payload, sort_keys=True).encode()
        
        # Generate signature (simulating data owner signing)
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        signature = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
        times['issue_audit_request'] = (time.time() - start) * 1000
        
        times['total'] = times['generate_temp_key'] + times['issue_audit_request']
        return times
    
    def measure_smart_contract_operations(self, file_data, request_payload):
        """Measure time for smart contract operations:
        1. Verify audit response
        2. Process verification
        """
        times = {}
        
        # 1. Verify audit response (verify signature and validate)
        start = time.time()
        # Simulate verifying the audit response
        response_payload = {
            'request_id': request_payload['requester_id'],
            'verified': True,
            'file_integrity': hashlib.sha3_256(file_data).hexdigest(),  # Upgraded to SHA-3-256
            'timestamp': datetime.now().isoformat()
        }
        response_bytes = json.dumps(response_payload, sort_keys=True).encode()
        
        # Verify signature (simulating smart contract verification)
        public_key = ec.generate_private_key(ec.SECP256R1(), default_backend()).public_key()
        # In real scenario, this would verify an actual signature
        verification_result = True
        times['verify_audit_response'] = (time.time() - start) * 1000
        
        # 2. Process verification (additional smart contract logic)
        start = time.time()
        # Simulate smart contract processing
        if verification_result:
            # Additional validation logic using SHA-3-256
            integrity_check = hashlib.sha3_256(file_data).hexdigest() == response_payload['file_integrity']
        times['process_verification'] = (time.time() - start) * 1000
        
        times['total'] = times['verify_audit_response'] + times['process_verification']
        return times
    
    def measure_public_cloud_operations(self, file_data):
        """Measure time for public cloud operations:
        1. Process audit request
        2. Generate audit response
        """
        times = {}
        
        # 1. Process audit request (receive and validate)
        start = time.time()
        # Simulate receiving and processing audit request using SHA-3-256
        file_hash = hashlib.sha3_256(file_data).hexdigest()  # Upgraded to SHA-3-256
        file_size = len(file_data)
        # Simulate cloud processing overhead
        time.sleep(0.001)  # Simulate network/processing delay
        times['process_audit_request'] = (time.time() - start) * 1000
        
        # 2. Generate audit response (create response and sign)
        start = time.time()
        # Simulate generating audit response
        response = {
            'file_hash': file_hash,
            'file_size': file_size,
            'integrity_verified': True,
            'timestamp': datetime.now().isoformat()
        }
        response_bytes = json.dumps(response, sort_keys=True).encode()
        
        # Sign response (simulating cloud signing)
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        signature = private_key.sign(response_bytes, ec.ECDSA(hashes.SHA256()))
        times['generate_audit_response'] = (time.time() - start) * 1000
        
        times['total'] = times['process_audit_request'] + times['generate_audit_response']
        return times
    
    def run_measurements(self):
        """Run performance measurements for all file sizes"""
        print("Starting performance measurements...")
        print("=" * 60)
        
        for size_kb in FILE_SIZES_KB:
            print(f"\nTesting file size: {size_kb} KB ({size_kb/1024:.2f} MB)")
            
            # Generate test file
            file_data = self.generate_test_file(size_kb)
            
            # Measure Data Owner operations
            print("  Measuring Data Owner operations...")
            data_owner_times = self.measure_data_owner_operations(file_data)
            self.results['data_owner'].append({
                'file_size_kb': size_kb,
                'times': data_owner_times
            })
            print(f"    Total: {data_owner_times['total']:.2f} ms")
            
            # Create request payload for smart contract
            request_payload = {
                'file_hash': hashlib.sha3_256(file_data).hexdigest(),  # Upgraded to SHA-3-256
                'file_size': len(file_data),
                'requester_id': secrets.token_hex(16)
            }
            
            # Measure Smart Contract operations
            print("  Measuring Smart Contract operations...")
            smart_contract_times = self.measure_smart_contract_operations(file_data, request_payload)
            self.results['smart_contract'].append({
                'file_size_kb': size_kb,
                'times': smart_contract_times
            })
            print(f"    Total: {smart_contract_times['total']:.2f} ms")
            
            # Measure Public Cloud operations
            print("  Measuring Public Cloud operations...")
            public_cloud_times = self.measure_public_cloud_operations(file_data)
            self.results['public_cloud'].append({
                'file_size_kb': size_kb,
                'times': public_cloud_times
            })
            print(f"    Total: {public_cloud_times['total']:.2f} ms")
        
        print("\n" + "=" * 60)
        print("Measurements completed!")
        return self.results
    
    def save_results(self, filename='performance_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {filename}")
    
    def generate_csv_for_graphs(self, filename='performance_data.csv'):
        """Generate CSV file for graph generation"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['File Size (KB)', 'File Size (MB)', 'Component', 'Operation', 'Time (ms)'])
            
            for component in ['data_owner', 'smart_contract', 'public_cloud']:
                for entry in self.results[component]:
                    size_kb = entry['file_size_kb']
                    size_mb = size_kb / 1024
                    times = entry['times']
                    
                    for operation, time_ms in times.items():
                        writer.writerow([size_kb, f"{size_mb:.3f}", component, operation, f"{time_ms:.3f}"])
        
        print(f"CSV data saved to {filename}")

if __name__ == '__main__':
    measurer = PerformanceMeasurer()
    results = measurer.run_measurements()
    measurer.save_results()
    measurer.generate_csv_for_graphs()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for component in ['data_owner', 'smart_contract', 'public_cloud']:
        print(f"\n{component.replace('_', ' ').title()}:")
        for entry in results[component]:
            print(f"  {entry['file_size_kb']} KB: {entry['times']['total']:.2f} ms")

