import requests, json

BASE = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
T = 90
p1 = {}
p2 = {}

# PHASE 1 CHECKS
r = requests.get(f"{BASE}/health", timeout=T)
p1["health"] = "PASS" if r.status_code==200 else f"FAIL {r.status_code}"

r = requests.post(f"{BASE}/reset", timeout=T)
p1["reset_POST"] = "PASS" if r.status_code==200 and "task_id" in r.json() else f"FAIL {r.text[:100]}"

r = requests.get(f"{BASE}/tasks", timeout=T)
tasks = r.json() if r.status_code==200 else []
p1["tasks_3plus"] = f"PASS ({len(tasks)} tasks)" if len(tasks)>=3 else f"FAIL only {len(tasks)}"

r = requests.get(f"{BASE}/state", timeout=T)
p1["state"] = "PASS" if r.status_code==200 else f"FAIL {r.status_code}"

print("=== PHASE 1 RESULTS ===")
for k,v in p1.items(): print(f"  {k}: {v}")

# PHASE 2 CHECKS
print("\n=== PHASE 2 RESULTS ===")
for task in tasks:
    tid = task['task_id']
    try:
        obs = requests.post(f"{BASE}/reset?task_id={tid}", timeout=T).json()
        query = obs.get('current_query','SELECT 1')
        action = {"optimized_query": query, "identified_pattern": "NONE",
                 "explanation": "test", "index_statements": [], "schema_analysis": ""}
        step = requests.post(f"{BASE}/step", json=action, timeout=T).json()
        r = step.get('reward', -1)
        status = "PASS" if 0.0 < float(r) < 1.0 else f"FAIL reward={r}"
        p2[tid] = status
        print(f"  {tid}: {status}")
    except Exception as e:
        p2[tid] = f"ERROR: {e}"
        print(f"  {tid}: ERROR {e}")

all_p2 = all("PASS" in v for v in p2.values())
all_p1 = all("PASS" in v for v in p1.values())
print(f"\nPHASE 1: {'ALL PASSED' if all_p1 else 'FAILED'}")
print(f"PHASE 2: {'ALL PASSED' if all_p2 else 'SCORE BOUNDARY ISSUES REMAIN'}")
