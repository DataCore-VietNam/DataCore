#!/usr/bin/env python3
"""
Simple API Call Test - Call preview endpoint to test connectivity
"""

import requests
from dotenv import dotenv_values
import os
import json

# Load .env for sensitive keys only
_env = dotenv_values()

print("=" * 70)
print("DATACORE API - SIMPLE TEST CALL")
print("=" * 70)

# API key from .env only, URLs from environment
preview_url = os.getenv("DATACORE_PREVIEW_URL", "https://gateway.datacore.vn/data/ds/preview")
api_key = _env.get("X_DATACORE_API_KEY", "your_api_key_here")

print(f"\nConfiguration:")
print(f"  Preview URL: {preview_url}")
print(f"  API Key: {api_key[:15]}..." if api_key != "your_api_key_here" else "  API Key: NOT SET (using placeholder)")

# Test 1: Preview without auth
print(f"\n[TEST 1] Preview endpoint without auth")
print("-" * 70)

try:
    response = requests.get(
        preview_url,
        params={"dataSetCode": "vsic"},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        if data.get('data'):
            fields = data['data'].get('fields', [])
            records = data['data'].get('dataDetail', [])
            print(f"Fields: {len(fields)} columns")
            print(f"Records: {len(records)} rows")
            
            if fields:
                print(f"Column names: {[f.get('name', 'unknown') for f in fields[:5]]}")
            if records and len(records) > 0:
                print(f"First record keys: {list(records[0].keys())[:5]}")
        print("\nResponse (truncated):")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:300] + "...")
    else:
        print(f"Error: {response.text[:200]}")
        
except requests.RequestException as e:
    print(f"Request Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Preview with API Key
print(f"\n[TEST 2] Preview endpoint with API Key")
print("-" * 70)

headers = {"x-api-key": api_key}

try:
    response = requests.get(
        preview_url,
        params={"dataSetCode": "vsic"},
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        if data.get('data'):
            fields = data['data'].get('fields', [])
            records = data['data'].get('dataDetail', [])
            print(f"Fields: {len(fields)} columns")
            print(f"Records: {len(records)} rows")
    else:
        print(f"Error: {response.text[:200]}")
        
except requests.RequestException as e:
    print(f"Request Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: List datasets
print(f"\n[TEST 3] List datasets endpoint")
print("-" * 70)

list_url = os.getenv("DATACORE_LIST_URL", "https://gateway.datacore.vn/data/ds/list")

try:
    response = requests.get(list_url, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Status: {data.get('status')}")
        
        if isinstance(data.get('data'), list):
            print(f"Datasets found: {len(data['data'])}")
            for ds in data['data'][:3]:
                print(f"  - {ds}")
    else:
        print(f"Error: {response.text[:200]}")
        
except requests.RequestException as e:
    print(f"Request Error: {e}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("Tests completed!")
print("=" * 70)
