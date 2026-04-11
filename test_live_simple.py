#!/usr/bin/env python3
"""
Simple test with retries for HuggingFace Space (handles cold starts).
"""

import requests
import json
import time

BASE_URL = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
TIMEOUT = 60  # Longer timeout for cold starts
MAX_RETRIES = 3

def test_with_retry(method, endpoint, body=None, retries=MAX_RETRIES):
    """Test endpoint with retry logic for cold starts."""
    url = f"{BASE_URL}{endpoint}"
    
    for attempt in range(retries):
        try:
            print(f"\n{'🔄' if attempt > 0 else '🔍'} {method} {endpoint} (attempt {attempt + 1}/{retries})")
            
            if method == "GET":
                response = requests.get(url, timeout=TIMEOUT)
            else:
                response = requests.post(url, json=body, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Status: {response.status_code}")
                return data
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout after {TIMEOUT}s")
            if attempt < retries - 1:
                wait = 10 * (attempt + 1)
                print(f"   Waiting {wait}s before retry (Space may be waking up)...")
                time.sleep(wait)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(5)
    
    print(f"❌ Failed after {retries} attempts")
    return None

def main():
    print("="*70)
    print("  TESTING LIVE HUGGINGFACE SPACE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s per request")
    print(f"Max retries: {MAX_RETRIES}")
    print("\nNote: First request may take 30-60s if Space is sleeping...")
    
    # Test 1: Health check
    print("\n" + "="*70)
    print("TEST 1: GET /health")
    print("="*70)
    health = test_with_retry("GET", "/health")
    if health:
        print(f"\n📊 Health Response:")
        print(json.dumps(health, indent=2))
        if health.get("status") == "ok":
            print("\n✅ PASS: Health check OK")
        else:
            print(f"\n❌ FAIL: Status is '{health.get('status')}', expected 'ok'")
    else:
        print("\n❌ FAIL: Health endpoint not responding")
        print("\n⚠️  Your Space may be:")
        print("   1. Still building/deploying")
        print("   2. In sleep mode (try accessing it in browser first)")
        print("   3. Having runtime errors")
        print(f"\n   Visit: {BASE_URL} to check status")
        return
    
    time.sleep(2)
    
    # Test 2: Tasks
    print("\n" + "="*70)
    print("TEST 2: GET /tasks")
    print("="*70)
    tasks = test_with_retry("GET", "/tasks")
    if tasks and isinstance(tasks, list):
        print(f"\n✅ PASS: Found {len(tasks)} tasks")
        for i, task in enumerate(tasks[:3]):
            print(f"   {i+1}. {task.get('task_id')} - {task.get('expected_pattern')}")
    else:
        print(f"\n❌ FAIL: Expected list of tasks, got: {type(tasks)}")
    
    time.sleep(2)
    
    # Test 3: Reset
    print("\n" + "="*70)
    print("TEST 3: POST /reset")
    print("="*70)
    reset = test_with_retry("POST", "/reset")
    if reset and "task_id" in reset:
        print(f"\n✅ PASS: Reset successful")
        print(f"   Task: {reset.get('task_id')}")
        print(f"   Pattern: {reset.get('expected_pattern')}")
    else:
        print(f"\n❌ FAIL: Invalid reset response")
    
    time.sleep(2)
    
    # Test 4: Reset with specific task
    print("\n" + "="*70)
    print("TEST 4: POST /reset?task_id=pds_select_star")
    print("="*70)
    reset_pds = test_with_retry("POST", "/reset?task_id=pds_select_star")
    if reset_pds and reset_pds.get("task_id") == "pds_select_star":
        print(f"\n✅ PASS: Reset to pds_select_star")
    else:
        print(f"\n❌ FAIL: Expected pds_select_star, got {reset_pds.get('task_id') if reset_pds else None}")
    
    time.sleep(2)
    
    # Test 5: Step with reward validation
    print("\n" + "="*70)
    print("TEST 5: POST /step (REWARD VALIDATION)")
    print("="*70)
    
    action = {
        "optimized_query": "SELECT allotment_id, state_code FROM pds_allotments WHERE state_code='MH'",
        "identified_pattern": "SELECT_STAR",
        "explanation": "Removed SELECT * to reduce bandwidth",
        "index_statements": ["CREATE INDEX idx_state ON pds_allotments(state_code)"],
        "schema_analysis": "No index on state_code"
    }
    
    step = test_with_retry("POST", "/step", action)
    if step:
        print(f"\n📊 Step Response:")
        print(json.dumps(step, indent=2)[:800])
        
        # Extract reward
        reward = step.get("reward")
        if isinstance(reward, dict):
            reward_value = reward.get("total", 0)
        else:
            reward_value = reward
        
        print(f"\n💰 Reward: {reward_value}")
        print(f"   Type: {type(reward_value)}")
        
        # Validate reward
        if isinstance(reward_value, (int, float)):
            if reward_value == 0.0:
                print(f"\n❌ FAIL: Reward is exactly 0.0 (FORBIDDEN)")
            elif reward_value == 1.0:
                print(f"\n❌ FAIL: Reward is exactly 1.0 (FORBIDDEN)")
            elif reward_value <= 0.01:
                print(f"\n❌ FAIL: Reward {reward_value} is <= 0.01")
            elif reward_value >= 0.99:
                print(f"\n❌ FAIL: Reward {reward_value} is >= 0.99")
            elif 0.01 < reward_value < 0.99:
                print(f"\n✅ PASS: Reward {reward_value} is strictly between 0.01 and 0.99 ✓")
            else:
                print(f"\n❌ FAIL: Reward {reward_value} is invalid")
        else:
            print(f"\n❌ FAIL: Reward is not numeric: {type(reward_value)}")
        
        # Check other fields
        if "done" in step and isinstance(step["done"], bool):
            print(f"✅ 'done' field present: {step['done']}")
        else:
            print(f"❌ 'done' field missing or invalid")
        
        if "observation" in step and isinstance(step["observation"], dict):
            print(f"✅ 'observation' field present")
        else:
            print(f"❌ 'observation' field missing or invalid")
    else:
        print(f"\n❌ FAIL: Step endpoint not responding")
    
    print("\n" + "="*70)
    print("  TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
