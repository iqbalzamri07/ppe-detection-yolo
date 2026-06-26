#!/usr/bin/env python3
"""Debug script to find the issue with StatsService"""

import sys
sys.path.insert(0, '/Users/iqbalzamri/Documents/ai-study-codebase/ppe-detection')

print("Debugging StatsService Import Issue")
print("=" * 50)

# Test 1: Import the module
print("\n1. Importing stats module...")
try:
    import app.services.stats as stats_module
    print("   ✓ Module imported successfully")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Import the class
print("\n2. Importing StatsService class...")
try:
    from app.services.stats import StatsService
    print("   ✓ Class imported successfully")
except Exception as e:
    print(f"   ✗ Class import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create instance without calling start()
print("\n3. Creating StatsService instance (no start)...")
try:
    service = StatsService()
    print("   ✓ Instance created successfully")
except Exception as e:
    print(f"   ✗ Instance creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test basic methods
print("\n4. Testing basic methods...")
try:
    service.add_detection('Hardhat', 0.85)
    stats = service.get_stats()
    print(f"   ✓ Methods work. Total detections: {stats['total']}")
except Exception as e:
    print(f"   ✗ Method test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test reset method
print("\n5. Testing reset method...")
try:
    result = service.reset_stats()
    print(f"   ✓ Reset method works. Message: {result['message']}")
    stats_after = service.get_stats()
    print(f"   ✓ Stats after reset - Total: {stats_after['total']}")
except Exception as e:
    print(f"   ✗ Reset method failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test start() method (this might hang)
print("\n6. Testing start() method (might hang)...")
print("   (This test has a 5-second timeout)")
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("start() method timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)  # 5 second timeout

try:
    service.start()
    print("   ✓ start() method completed (unexpected)")
    service.stop()
except TimeoutError:
    print("   ⚠ start() method timed out (expected behavior)")
    print("   This indicates the threading is blocking")
except Exception as e:
    print(f"   ⚠ start() method error: {e}")

signal.alarm(0)  # Cancel the alarm

print("\n✓ Debug complete!")
print("\nConclusion: The StatsService works fine, but start() method may cause issues.")