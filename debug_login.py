#!/usr/bin/env python
"""
Debug Login Endpoint - Test different payload formats
"""

import requests
import json
import os

LOGIN_URL = os.getenv("DATACORE_LOGIN_URL")

print("=" * 80)
print("DEBUGGING LOGIN ENDPOINT")
print("=" * 80)

username = input("\nUsername (email): ").strip()
password = input("Password: ").strip()

if not username or not password:
    print("✗ Username and password required")
    exit(1)

# Test different payload formats
payloads = [
    {
        "name": "username + password",
        "data": {"username": username, "password": password}
    },
    {
        "name": "email + password",
        "data": {"email": username, "password": password}
    },
    {
        "name": "user + password",
        "data": {"user": username, "password": password}
    },
    {
        "name": "account + password",
        "data": {"account": username, "password": password}
    },
]

for test in payloads:
    print(f"\n{test['name']}")
    print("-" * 80)
    print(f"Payload: {json.dumps(test['data'], indent=2)}")
    
    try:
        response = requests.post(LOGIN_URL, json=test["data"], timeout=10)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check if token is in response
        token = result.get("access_token") or result.get("token")
        if token:
            print(f"✓ TOKEN FOUND: {token[:50]}...")
            print("✓ This payload format works!")
            break
        else:
            print(f"✗ No token in response")
            
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
