"""
Exact simulation of the hackathon Phase 2 validator.
Runs reset → step for ALL tasks, captures reward exactly as validator does.
Flags any score == 0.0 or == 1.0 as a boundary violation.
"""
import requests, json, sys, time

BASE = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
T = 120

TASKS = [
    "gst_missing_index",
    "gst_n_plus_one",
    "gst_multi_join",
    "pds_select_star",
    "railway_simple_filter",
    "pds_cartesian",
    "mgnrega_wildcard",
    "railway_tatkal_workload",
    "mgnrega_schema_e",
    "mgnrega_count",
    "railway_missing_index",
    "gst_unbounded_aggregation",
    "pds_n_plus_one",
    "mgnrega_implicit_cast",
]

ACTIONS = [
    {"optimized_query": "SELECT 1", "identified_pattern": "NONE", "explanation": "test", "index_statements": [], "schema_analysis": ""},
    {"optimized_query": "SELECT id FROM gst_invoice_records WHERE state_code = 'MH'", "identified_pattern": "MISSING_INDEX", "explanation": "use index", "index_statements": ["CREATE INDEX idx_state ON gst_invoice_records(state_code)"], "schema_analysis": ""},
    {"optimized_query": "SELECT card_id, district_code FROM ration_card_beneficiaries WHERE card_type = 'BPL'", "identified_pattern": "SELECT_STAR", "explanation": "remove star", "index_statements": [], "schema_analysis": ""},
]

failures = []
results = {}

print("=" * 60)
print("EXACT VALIDATOR SIMULATION — Phase 2")
print(f"Target: {BASE}")
print("=" * 60)

for tid in TASKS:
    print(f"\n[TASK] {tid}")
    task_results = []
    
    for action_idx, action in enumerate(ACTIONS):
        try:
            # Step 1: Reset
            r = requests.post(f"{BASE}/reset", 
                              params={"task_id": tid},
                              timeout=T)
            if r.status_code != 200:
                print(f"  ACTION {action_idx}: RESET FAILED {r.status_code}: {r.text[:100]}")
                task_results.append(f"RESET_FAIL_{r.status_code}")
                continue
            
            obs = r.json()
            actual_query = obs.get("current_query", "SELECT 1")
            
            # Use the actual query for one of our test actions
            if action_idx == 0:
                test_action = {
                    "optimized_query": actual_query,  # same query = no improvement baseline
                    "identified_pattern": "NONE",
                    "explanation": "baseline passthrough",
                    "index_statements": [],
                    "schema_analysis": ""
                }
            else:
                test_action = action
            
            # Step 2: Step
            s = requests.post(f"{BASE}/step", json=test_action, timeout=T)
            if s.status_code != 200:
                print(f"  ACTION {action_idx}: STEP FAILED {s.status_code}: {s.text[:100]}")
                task_results.append(f"STEP_FAIL_{s.status_code}")
                continue
            
            step_data = s.json()
            reward = step_data.get("reward", -999)
            reward_detail = step_data.get("reward_detail", {})
            
            try:
                reward = float(reward)
            except:
                reward = -999.0
            
            in_range = (0.0 < reward < 1.0)
            strict_exact = (reward == 0.0 or reward == 1.0)
            
            status = "✅ PASS" if in_range else f"❌ FAIL reward={reward}"
            print(f"  ACTION {action_idx}: reward={reward:.4f} → {status}")
            
            if not in_range:
                failures.append({
                    "task": tid,
                    "action": action_idx,
                    "reward": reward,
                    "detail": reward_detail,
                    "obs_task_id": obs.get("task_id"),
                })
            
            task_results.append(reward)
            
        except Exception as e:
            print(f"  ACTION {action_idx}: EXCEPTION {e}")
            task_results.append(f"ERROR_{e}")
        
        time.sleep(0.5)
    
    results[tid] = task_results

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_pass = len(failures) == 0

for tid, tr in results.items():
    nums = [r for r in tr if isinstance(r, float)]
    bads = [r for r in nums if not (0.0 < r < 1.0)]
    symbol = "✅" if not bads else "❌"
    print(f"  {symbol} {tid}: {tr}")

if failures:
    print(f"\n❌ {len(failures)} BOUNDARY VIOLATIONS FOUND:")
    for f in failures:
        print(f"  Task={f['task']} action={f['action']} reward={f['reward']}")
        print(f"    detail={json.dumps(f['detail'], indent=6)}")
else:
    print("\n✅ ALL SCORES STRICTLY IN (0.0, 1.0) — READY TO SUBMIT")

print(f"\nPHASE 2: {'ALL PASSED' if all_pass else 'FAILED — FIX NEEDED'}")
