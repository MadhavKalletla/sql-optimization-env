#!/usr/bin/env python3
"""
Test live HuggingFace Space endpoints to verify Phase 2 compliance.
All reward values must be strictly between 0.01 and 0.99.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
TIMEOUT = 30  # seconds

def print_header(text: str):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_test(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")

def test_get(endpoint: str, test_name: str) -> Optional[Dict[str, Any]]:
    """Test a GET endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"\n🔍 Testing: GET {endpoint}")
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_test(test_name, False, f"Status: {response.status_code}")
            print(f"       Response: {response.text[:500]}")
            return None
        
        data = response.json()
        return data
        
    except requests.exceptions.Timeout:
        print_test(test_name, False, f"Request timed out after {TIMEOUT}s")
        return None
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return None

def test_post(endpoint: str, body: Optional[Dict] = None, test_name: str = "") -> Optional[Dict[str, Any]]:
    """Test a POST endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"\n🔍 Testing: POST {endpoint}")
        if body:
            print(f"   Body: {json.dumps(body, indent=2)[:200]}...")
        
        response = requests.post(url, json=body, timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_test(test_name, False, f"Status: {response.status_code}")
            print(f"       Response: {response.text[:500]}")
            return None
        
        data = response.json()
        return data
        
    except requests.exceptions.Timeout:
        print_test(test_name, False, f"Request timed out after {TIMEOUT}s")
        return None
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return None

def verify_reward(reward: float, test_name: str) -> bool:
    """Verify reward is strictly between 0.01 and 0.99."""
    if reward <= 0.01 or reward >= 0.99:
        print_test(test_name, False, f"Reward {reward} is NOT strictly between 0.01 and 0.99")
        return False
    
    if reward == 0.0 or reward == 1.0:
        print_test(test_name, False, f"Reward is exactly {reward} (FORBIDDEN)")
        return False
    
    print_test(test_name, True, f"Reward = {reward} (valid range)")
    return True

def main():
    print_header("PHASE 2 VALIDATION - LIVE ENDPOINT TESTING")
    print(f"Base URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")
    
    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # ========================================================================
    # TEST 1: GET /health
    # ========================================================================
    print_header("TEST 1: GET /health")
    data = test_get("/health", "GET /health")
    if data:
        if data.get("status") == "ok":
            print_test("Health check", True, f"Status: {data.get('status')}")
            print(f"   Environment: {data.get('environment', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Total rows: {data.get('total_rows', 'N/A')}")
            results["passed"] += 1
        else:
            print_test("Health check", False, f"Status is not 'ok': {data.get('status')}")
            results["failed"] += 1
            results["errors"].append(f"Health status: {data}")
    else:
        results["failed"] += 1
        results["errors"].append("Health endpoint failed")
    
    time.sleep(1)
    
    # ========================================================================
    # TEST 2: GET /tasks
    # ========================================================================
    print_header("TEST 2: GET /tasks")
    data = test_get("/tasks", "GET /tasks")
    if data:
        if isinstance(data, list) and len(data) >= 3:
            print_test("Tasks list", True, f"Found {len(data)} tasks")
            for i, task in enumerate(data[:5]):
                print(f"   Task {i+1}: {task.get('task_id', 'N/A')} - {task.get('expected_pattern', 'N/A')}")
            results["passed"] += 1
        else:
            print_test("Tasks list", False, f"Expected 3+ tasks, got {len(data) if isinstance(data, list) else 'invalid'}")
            results["failed"] += 1
            results["errors"].append(f"Tasks response: {data}")
    else:
        results["failed"] += 1
        results["errors"].append("Tasks endpoint failed")
    
    time.sleep(1)
    
    # ========================================================================
    # TEST 3: POST /reset (no task_id)
    # ========================================================================
    print_header("TEST 3: POST /reset (no task_id)")
    data = test_post("/reset", None, "POST /reset")
    if data:
        required_fields = ["task_id", "slow_query", "expected_pattern", "tables"]
        missing = [f for f in required_fields if f not in data]
        if not missing:
            print_test("Reset observation", True, f"Task: {data.get('task_id')}")
            print(f"   Pattern: {data.get('expected_pattern')}")
            print(f"   Tables: {data.get('tables')}")
            results["passed"] += 1
        else:
            print_test("Reset observation", False, f"Missing fields: {missing}")
            results["failed"] += 1
            results["errors"].append(f"Reset response missing: {missing}")
    else:
        results["failed"] += 1
        results["errors"].append("Reset endpoint failed")
    
    time.sleep(1)
    
    # ========================================================================
    # TEST 4: GET /state
    # ========================================================================
    print_header("TEST 4: GET /state")
    data = test_get("/state", "GET /state")
    if data:
        required_fields = ["current_task_id", "episode_count"]
        missing = [f for f in required_fields if f not in data]
        if not missing:
            print_test("State", True, f"Task: {data.get('current_task_id')}")
            print(f"   Episode: {data.get('episode_count')}")
            results["passed"] += 1
        else:
            print_test("State", False, f"Missing fields: {missing}")
            results["failed"] += 1
            results["errors"].append(f"State response missing: {missing}")
    else:
        results["failed"] += 1
        results["errors"].append("State endpoint failed")
    
    time.sleep(1)
    
    # ========================================================================
    # TEST 5-7: POST /reset with specific task_ids
    # ========================================================================
    test_tasks = [
        "pds_select_star",
        "gst_missing_index",
        "gst_n_plus_one"
    ]
    
    for task_id in test_tasks:
        print_header(f"TEST: POST /reset?task_id={task_id}")
        data = test_post(f"/reset?task_id={task_id}", None, f"Reset {task_id}")
        
        if data:
            if data.get("task_id") == task_id:
                print_test(f"Reset {task_id}", True, f"Pattern: {data.get('expected_pattern')}")
                results["passed"] += 1
            else:
                print_test(f"Reset {task_id}", False, f"Got task_id: {data.get('task_id')}")
                results["failed"] += 1
                results["errors"].append(f"Reset {task_id} returned wrong task")
        else:
            results["failed"] += 1
            results["errors"].append(f"Reset {task_id} failed")
        
        time.sleep(1)
    
    # ========================================================================
    # TEST 8-10: POST /step for each task with reward validation
    # ========================================================================
    print_header("REWARD VALIDATION TESTS")
    
    step_actions = {
        "pds_select_star": {
            "optimized_query": "SELECT allotment_id, state_code, district_code FROM pds_allotments WHERE state_code='MH'",
            "identified_pattern": "SELECT_STAR",
            "explanation": "Removed SELECT * to avoid full column scan and reduce bandwidth",
            "index_statements": ["CREATE INDEX idx_state ON pds_allotments(state_code)"],
            "schema_analysis": "No index on state_code column"
        },
        "gst_missing_index": {
            "optimized_query": "SELECT invoice_id, gstin_supplier FROM gst_invoice_records WHERE state_code='MH'",
            "identified_pattern": "MISSING_INDEX",
            "explanation": "Added index on state_code to avoid full table scan",
            "index_statements": ["CREATE INDEX idx_gst_state ON gst_invoice_records(state_code)"],
            "schema_analysis": "Missing index on frequently queried state_code column"
        },
        "gst_n_plus_one": {
            "optimized_query": "SELECT r.invoice_id, r.gstin_supplier, i.item_description FROM gst_invoice_records r JOIN gst_invoice_items i ON r.invoice_id = i.invoice_id WHERE r.state_code='MH'",
            "identified_pattern": "N_PLUS_ONE",
            "explanation": "Replaced correlated subquery with JOIN to eliminate N+1 query pattern",
            "index_statements": ["CREATE INDEX idx_invoice ON gst_invoice_items(invoice_id)"],
            "schema_analysis": "Correlated subquery causes N+1 queries"
        }
    }
    
    for task_id in test_tasks:
        print_header(f"STEP TEST: {task_id}")
        
        # First reset to the specific task
        reset_data = test_post(f"/reset?task_id={task_id}", None, f"Reset for step {task_id}")
        if not reset_data:
            print_test(f"Step {task_id}", False, "Reset failed before step")
            results["failed"] += 1
            results["errors"].append(f"Step {task_id}: reset failed")
            continue
        
        time.sleep(1)
        
        # Now send the step action
        action = step_actions.get(task_id, step_actions["pds_select_star"])
        step_data = test_post("/step", action, f"Step {task_id}")
        
        if step_data:
            print(f"\n📊 Step Response for {task_id}:")
            print(json.dumps(step_data, indent=2)[:1000])
            
            # Verify required fields
            required_fields = ["reward", "done", "observation"]
            missing = [f for f in required_fields if f not in step_data]
            
            if missing:
                print_test(f"Step {task_id} - fields", False, f"Missing: {missing}")
                results["failed"] += 1
                results["errors"].append(f"Step {task_id} missing fields: {missing}")
                continue
            
            # Check reward value
            reward = step_data.get("reward")
            if isinstance(reward, dict):
                # If reward is an object, get the total
                reward_value = reward.get("total", reward.get("reward", 0))
            else:
                reward_value = reward
            
            print(f"\n💰 Reward Analysis:")
            print(f"   Raw reward: {reward}")
            print(f"   Reward value: {reward_value}")
            print(f"   Type: {type(reward_value)}")
            
            # Verify reward is strictly between 0.01 and 0.99
            if isinstance(reward_value, (int, float)):
                if 0.01 < reward_value < 0.99:
                    print_test(f"Step {task_id} - reward", True, f"Reward = {reward_value} ✓")
                    results["passed"] += 1
                else:
                    print_test(f"Step {task_id} - reward", False, f"Reward {reward_value} NOT in (0.01, 0.99)")
                    results["failed"] += 1
                    results["errors"].append(f"Step {task_id}: reward = {reward_value}")
                    print(f"\n⚠️  FULL RESPONSE:")
                    print(json.dumps(step_data, indent=2))
            else:
                print_test(f"Step {task_id} - reward", False, f"Reward is not numeric: {type(reward_value)}")
                results["failed"] += 1
                results["errors"].append(f"Step {task_id}: reward type = {type(reward_value)}")
            
            # Check done field
            done = step_data.get("done")
            if isinstance(done, bool):
                print_test(f"Step {task_id} - done", True, f"Done = {done}")
                results["passed"] += 1
            else:
                print_test(f"Step {task_id} - done", False, f"Done is not boolean: {done}")
                results["failed"] += 1
            
            # Check observation field
            observation = step_data.get("observation")
            if isinstance(observation, dict) and "task_id" in observation:
                print_test(f"Step {task_id} - observation", True, f"Valid observation")
                results["passed"] += 1
            else:
                print_test(f"Step {task_id} - observation", False, f"Invalid observation")
                results["failed"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(f"Step {task_id} failed")
        
        time.sleep(2)  # Longer delay between step tests
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("FINAL RESULTS")
    print(f"\n✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Total:  {results['passed'] + results['failed']}")
    
    if results['errors']:
        print(f"\n⚠️  ERRORS FOUND:")
        for i, error in enumerate(results['errors'], 1):
            print(f"   {i}. {error}")
    
    if results['failed'] == 0:
        print(f"\n🎉 ALL TESTS PASSED! Your HuggingFace Space is Phase 2 compliant!")
        return 0
    else:
        print(f"\n❌ {results['failed']} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
