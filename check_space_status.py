#!/usr/bin/env python3
"""Quick diagnostic to check HuggingFace Space status."""

import requests
import time

BASE_URL = "https://kalletlamadhav-sql-optimized-env-new.hf.space"

print("="*70)
print("HUGGINGFACE SPACE DIAGNOSTIC")
print("="*70)
print(f"URL: {BASE_URL}")
print("\nAttempting connection...")

try:
    # Try with a very short timeout first
    print("\n1. Quick ping (5s timeout)...")
    response = requests.get(BASE_URL, timeout=5)
    print(f"   ✅ Connected! Status: {response.status_code}")
    print(f"   Content length: {len(response.text)} bytes")
    print(f"   First 200 chars: {response.text[:200]}")
except requests.exceptions.Timeout:
    print("   ⏱️  Timeout - Space may be sleeping or slow")
except requests.exceptions.ConnectionError as e:
    print(f"   ❌ Connection error: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2. Trying /health endpoint (10s timeout)...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"   ✅ Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")
    else:
        print(f"   Response: {response.text[:300]}")
except requests.exceptions.Timeout:
    print("   ⏱️  Timeout after 10s")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("RECOMMENDATIONS:")
print("="*70)
print("1. Visit the Space URL in your browser to wake it up:")
print(f"   {BASE_URL}")
print("\n2. Check the Space logs on HuggingFace:")
print(f"   https://huggingface.co/spaces/kalletlamadhav/sql-optimized-env-new")
print("\n3. Verify the Space is running (not building or crashed)")
print("\n4. If Space is sleeping, it may take 30-60s to wake up")
print("="*70)
