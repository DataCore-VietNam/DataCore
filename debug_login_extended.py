#!/usr/bin/env python
"""
Debug Login Endpoint - Extended Tests
"""

import requests
import json
import os

LOGIN_URL = os.getenv("DATACORE_LOGIN_URL")

print("=" * 80)
print("EXTENDED LOGIN DEBUGGING")
print("=" * 80)

username = input("\nUsername (email): ").strip()
password = input("Password: ").strip()

if not username or not password:
    print("✗ Username and password required")
    exit(1)

# Test with different variations
payloads = [
    {
        "name": "With only username (no password)",
        "data": {"username": username}
    },
    {
        "name": "With only password (no username)",
        "data": {"password": password}
    },
    {
        "name": "Empty payload",
        "data": {}
    },
    {
        "name": "With additional fields: client_id",
        "data": {"username": username, "password": password, "client_id": ""}
    },
    {
        "name": "username in different case: Username",
        "data": {"Username": username, "password": password}
    },
    {
        "name": "Lowercase password",
        "data": {"username": username, "passwd": password}
    },
]

for test in payloads:
    print(f"\n{test['name']}")
    print("-" * 80)
    print(f"Payload: {json.dumps(test['data'])}")
    
    try:
        response = requests.post(LOGIN_URL, json=test["data"], timeout=10)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: message='{result.get('message')}' | status={result.get('status')}")
        
        # Check if token is in response
        token = result.get("access_token") or result.get("token") or result.get("data", {}).get("token")
        if token:
            print(f"✓ TOKEN FOUND: {token[:30]}...")
            
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("\nIf error persists, possible issues:")
print("1. Username/email doesn't exist in the system")
print("2. Password is incorrect")
print("3. Account might be suspended or inactive")
print("4. The endpoint requires additional fields we haven't tried")
print("=" * 80)
