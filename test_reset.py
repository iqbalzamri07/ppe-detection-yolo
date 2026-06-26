#!/usr/bin/env python3
"""Test script for stats service reset functionality"""

import sys
sys.path.insert(0, '/Users/iqbalzamri/Documents/ai-study-codebase/ppe-detection')

from collections import defaultdict
from datetime import datetime

class SimpleStatsService:
    """Simplified stats service for testing"""
    
    def __init__(self):
        self.stats = {
            'total': 0,
            'compliance': 0,
            'violations': 0,
            'other': 0,
            'detections': [],
            'hourly_data': defaultdict(int),
            'class_counts': defaultdict(int),
            'alerts': []
        }
        
        self.compliance_classes = ['Hardhat', 'Mask', 'Safety Vest']
        self.violation_classes = ['NO-Hardhat', 'NO-Mask', 'NO-Safety Vest']
    
    def add_detection(self, class_name: str, confidence: float):
        """Add a test detection"""
        now = datetime.now()
        hour = now.hour
        
        detection = {
            'class': class_name,
            'confidence': round(confidence * 100, 2),
            'time': now.isoformat(),
            'hour': hour
        }
        
        self.stats['total'] += 1
        self.stats['hourly_data'][hour] += 1
        self.stats['class_counts'][class_name] += 1
        
        if class_name in self.compliance_classes:
            self.stats['compliance'] += 1
            detection['type'] = 'compliance'
        elif class_name in self.violation_classes:
            self.stats['violations'] += 1
            detection['type'] = 'violation'
        else:
            self.stats['other'] += 1
            detection['type'] = 'other'
        
        self.stats['detections'].insert(0, detection)
    
    def get_stats(self):
        """Get current statistics"""
        total_detections = self.stats['total']
        compliance_rate = 0
        if total_detections > 0:
            compliance_rate = round((self.stats['compliance'] / total_detections) * 100, 1)
        
        hourly_list = [self.stats['hourly_data'][i] for i in range(24)]
        
        return {
            'total': total_detections,
            'compliance': self.stats['compliance'],
            'violations': self.stats['violations'],
            'other': self.stats['other'],
            'compliance_rate': compliance_rate,
            'hourly_data': hourly_list,
            'class_counts': dict(self.stats['class_counts']),
            'last_updated': datetime.now().isoformat()
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            'total': 0,
            'compliance': 0,
            'violations': 0,
            'other': 0,
            'detections': [],
            'hourly_data': defaultdict(int),
            'class_counts': defaultdict(int),
            'alerts': []
        }
        return {'message': 'Statistics reset successfully', 'stats': self.get_stats()}

# Test the functionality
print("Testing Stats Service Reset Functionality")
print("=" * 50)

service = SimpleStatsService()

# Add some test detections
print("\n1. Adding test detections...")
service.add_detection('Hardhat', 0.85)
service.add_detection('NO-Hardhat', 0.92)
service.add_detection('Mask', 0.78)
service.add_detection('Person', 0.95)
service.add_detection('Safety Vest', 0.88)

stats_before = service.get_stats()
print(f"   Total detections: {stats_before['total']}")
print(f"   Compliance: {stats_before['compliance']}")
print(f"   Violations: {stats_before['violations']}")
print(f"   Compliance rate: {stats_before['compliance_rate']}%")

# Reset statistics
print("\n2. Resetting statistics...")
reset_result = service.reset_stats()
print(f"   Reset message: {reset_result['message']}")

# Check stats after reset
print("\n3. Checking statistics after reset...")
stats_after = service.get_stats()
print(f"   Total detections: {stats_after['total']}")
print(f"   Compliance: {stats_after['compliance']}")
print(f"   Violations: {stats_after['violations']}")
print(f"   Compliance rate: {stats_after['compliance_rate']}%")
print(f"   Hourly data: {stats_after['hourly_data'][:5]}...")  # Show first 5 hours

# Verify reset worked
print("\n4. Verification:")
if stats_after['total'] == 0 and stats_after['compliance'] == 0:
    print("   ✓ Statistics reset successfully!")
else:
    print("   ✗ Statistics reset failed!")
    sys.exit(1)

print("\n✓ All tests passed!")