#!/usr/bin/env python3
"""Simple test to verify the reset API endpoint works"""

import sys
sys.path.insert(0, '/Users/iqbalzamri/Documents/ai-study-codebase/ppe-detection')

from app.services.stats import StatsService
from collections import defaultdict
from datetime import datetime

print("Testing Stats Service Import and Reset")
print("=" * 50)

# Test without threading
print("\n1. Creating StatsService instance (without threading)...")
try:
    service = StatsService()
    print("   ✓ StatsService created successfully")
except Exception as e:
    print(f"   ✗ Error creating StatsService: {e}")
    sys.exit(1)

# Add test data
print("\n2. Adding test detections...")
try:
    service.add_detection('Hardhat', 0.85)
    service.add_detection('NO-Hardhat', 0.92)
    service.add_detection('Mask', 0.78)
    
    stats_before = service.get_stats()
    print(f"   Total detections: {stats_before['total']}")
    print(f"   Compliance: {stats_before['compliance']}")
    print(f"   Violations: {stats_before['violations']}")
except Exception as e:
    print(f"   ✗ Error adding detections: {e}")
    sys.exit(1)

# Test reset
print("\n3. Testing reset_stats method...")
try:
    reset_result = service.reset_stats()
    print(f"   Reset message: {reset_result['message']}")
    
    if 'stats' in reset_result:
        stats_after = reset_result['stats']
        print(f"   Stats after reset:")
        print(f"   - Total: {stats_after['total']}")
        print(f"   - Compliance: {stats_after['compliance']}")
        print(f"   - Violations: {stats_after['violations']}")
        print(f"   - Compliance rate: {stats_after['compliance_rate']}%")
    else:
        print("   ⚠ Reset result doesn't contain 'stats' field")
        stats_after = service.get_stats()
        print(f"   Manually fetched stats:")
        print(f"   - Total: {stats_after['total']}")
        print(f"   - Compliance: {stats_after['compliance']}")
        print(f"   - Violations: {stats_after['violations']}")
        
except Exception as e:
    print(f"   ✗ Error during reset: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify reset worked
print("\n4. Verification...")
if stats_after['total'] == 0:
    print("   ✓ Statistics reset successfully!")
else:
    print(f"   ✗ Statistics reset failed! Total is still {stats_after['total']}")
    sys.exit(1)

print("\n✓ All tests passed!")