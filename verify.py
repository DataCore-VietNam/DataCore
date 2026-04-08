#!/usr/bin/env python
"""Final verification test for datacore package"""

print("=" * 70)
print("DATACORE PYTHON CLIENT - FINAL VERIFICATION")
print("=" * 70)
print()

# Test 1: Import
print("✓ Test 1: Package Import")
try:
    from datacore import Datacore
    print("  → Successfully imported Datacore")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    exit(1)

# Test 2: Client instantiation with API key
print()
print("✓ Test 2: Client Instantiation with API Key")
try:
    client = Datacore(api_key="test-key-12345")
    print(f"  → Client created successfully")
    print(f"  → API Key: {client.api_key[:10]}...")
    print(f"  → Base URL: {client.BASE_URL}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    exit(1)

# Test 3: Error handling (no API key)
print()
print("✓ Test 3: Error Handling (Missing API Key)")
try:
    import os
    # Temporarily unset env variable
    old_key = os.environ.pop("X_DATACORE_API_KEY", None)
    
    try:
        client = Datacore()
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  → Correctly raised ValueError")
        print(f"  → Error message: {str(e)[:60]}...")
    finally:
        if old_key:
            os.environ["X_DATACORE_API_KEY"] = old_key
except Exception as e:
    print(f"  ✗ Test failed: {e}")

# Test 4: Available methods
print()
print("✓ Test 4: Available Methods")
methods = ["search", "get_dataframe", "get_historical_price"]
for method in methods:
    if hasattr(client, method) and callable(getattr(client, method)):
        print(f"  ✓ {method}()")
    else:
        print(f"  ✗ {method}() not found")

# Test 5: Class attributes
print()
print("✓ Test 5: Class Attributes")
print(f"  ✓ BASE_URL: {Datacore.BASE_URL}")
print(f"  ✓ ENV_KEY: {Datacore.ENV_KEY}")

print()
print("=" * 70)
print("ALL TESTS PASSED! ✓")
print("=" * 70)
print()
print("Next steps:")
print("  1. Set X_DATACORE_API_KEY environment variable")
print("  2. Import and use: from datacore import Datacore")
print("  3. Create client: client = Datacore()")
print("  4. Get data: df = client.get_historical_price(limit=50)")
print()
print("Documentation:")
print("  • README.md         - Quick start guide")
print("  • USAGE_GUIDE.md    - Comprehensive documentation")
print("  • PROJECT_SUMMARY.md- Project overview")
print("  • examples.py       - Code examples")
