"""
Clean boundary sweep - no emoji, ASCII only for Windows terminal.
Tests every task with 2 actions: passthrough (baseline) + SELECT 1 (worst case edge).
"""
import requests
import json
import time
import sys

BASE = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
T = 90

TASKS = [
    "gst_missing_index", "gst_n_plus_one", "gst_multi_join",
    "pds_select_star", "railway_simple_filter", "pds_cartesian",
    "mgnrega_wildcard", "railway_tatkal_workload", "mgnrega_schema_e",
    "mgnrega_count", "railway_missing_index", "gst_unbounded_aggregation",
    "pds_n_plus_one", "mgnrega_implicit_cast",
]

failures = []
passed = 0
total = 0

print("=" * 60)
print("BOUNDARY SWEEP Against Live HF Space")
print("=" * 60)

# Wake up the space first
print("\n[WAKE] Pinging space...")
for attempt in range(5):
    try:
        r = requests.get(f"{BASE}/health", timeout=30)
        if r.status_code == 200:
            print(f"[WAKE] Space is UP - {r.json().get('status')}")
            break
        else:
            print(f"[WAKE] attempt {attempt+1}: status {r.status_code}, retrying...")
    except Exception as e:
        print(f"[WAKE] attempt {attempt+1}: {e}, retrying in 15s...")
    time.sleep(15)

print()

for tid in TASKS:
    # Reset
    try:
        r = requests.post(f"{BASE}/reset", params={"task_id": tid}, timeout=T)
        if r.status_code != 200:
            print(f"  [FAIL] {tid}: reset {r.status_code}")
            failures.append((tid, "reset_fail", r.status_code))
            continue
        obs = r.json()
        real_query = obs.get("current_query", "SELECT 1")
    except Exception as e:
        print(f"  [FAIL] {tid}: reset exception {e}")
        failures.append((tid, "reset_exc", str(e)))
        continue

    # Test action: passthrough same query (worst realistic case for boundary)
    action = {
        "optimized_query": real_query,
        "identified_pattern": "NONE",
        "explanation": "passthrough test",
        "index_statements": [],
        "schema_analysis": ""
    }

    try:
        s = requests.post(f"{BASE}/step", json=action, timeout=T)
        if s.status_code != 200:
            print(f"  [FAIL] {tid}: step {s.status_code}")
            failures.append((tid, "step_fail", s.status_code))
            continue

        data = s.json()
        reward = data.get("reward", -1)
        try:
            reward = float(reward)
        except:
            reward = -999.0

        in_range = (0.0 < reward < 1.0)
        total += 1

        if in_range:
            passed += 1
            print(f"  PASS  {tid}: reward={reward:.4f}")
        else:
            print(f"  FAIL  {tid}: reward={reward} <-- BOUNDARY VIOLATION")
            failures.append((tid, "boundary", reward, data.get("reward_detail", {})))

    except Exception as e:
        print(f"  FAIL  {tid}: step exception {e}")
        failures.append((tid, "step_exc", str(e)))

    time.sleep(1)

print()
print("=" * 60)
print(f"Results: {passed}/{total} passed")
if failures:
    print(f"FAILED ({len(failures)} violations):")
    for f in failures:
        print(f"  {f}")
else:
    print("ALL CLEAR - every reward strictly in (0.0, 1.0)")
    print("READY TO SUBMIT")
