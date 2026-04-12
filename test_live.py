import requests, time

BASE = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
T = 90
fails = []

def check(label, status, condition, detail=""):
    result = "PASS" if condition else "FAIL"
    print(f"{result} | {label} | {detail}")
    if not condition: fails.append(label)

print("Waiting a bit for Space to rebuild...")
time.sleep(120)

# Health
try:
    r = requests.get(f"{BASE}/health", timeout=T)
    check("GET /health", r.status_code, r.status_code==200, r.text[:100])
except Exception as e:
    check("GET /health", 0, False, str(e))

# Tasks
try:
    r = requests.get(f"{BASE}/tasks", timeout=T)
    tasks = r.json()
    check("GET /tasks", r.status_code, len(tasks)>=3, f"{len(tasks)} tasks found")
    task_ids = [t['task_id'] for t in tasks[:3]]
except Exception as e:
    check("GET /tasks", 0, False, str(e))
    task_ids = ['gst_missing_index','pds_select_star','railway_missing_index'] # fallback

# POST /reset for each task
for tid in task_ids:
    try:
        r = requests.post(f"{BASE}/reset?task_id={tid}", timeout=T)
        check(f"POST /reset {tid}", r.status_code, r.status_code==200, r.text[:150])
        if r.status_code == 200:
            obs = r.json()
            query = obs.get('current_query', 'SELECT 1')
            action = {"optimized_query": query, "identified_pattern": "NONE",
                     "explanation": "live test", "index_statements": [], "schema_analysis": "test"}
            r2 = requests.post(f"{BASE}/step", json=action, timeout=T)
            if r2.status_code == 200:
                reward = r2.json().get('reward', -1)
                check(f"POST /step {tid} reward in (0,1)", r2.status_code,
                     0.0 < reward < 1.0, f"reward={reward}")
            else:
                check(f"POST /step {tid}", r2.status_code, False, r2.text[:150])
    except Exception as e:
        check(f"POST /reset {tid}", 0, False, str(e))

# State
try:
    r = requests.get(f"{BASE}/state", timeout=T)
    check("GET /state", r.status_code, r.status_code==200, r.text[:100])
except Exception as e:
    check("GET /state", 0, False, str(e))

print(f"\n{'=== ALL LIVE TESTS PASSED ===' if not fails else 'FAILED: '+str(fails)}")
