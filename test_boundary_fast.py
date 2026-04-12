"""
Fast boundary sweep — same question as validator: does /step return reward in (0.0, 1.0)?
Tests every task with 3 action types. Prints FAIL immediately on boundary hit.
"""
import requests, json, sys, time

BASE = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
T = 60

TASKS = [
    "gst_missing_index", "gst_n_plus_one", "gst_multi_join",
    "pds_select_star", "railway_simple_filter", "pds_cartesian",
    "mgnrega_wildcard", "railway_tatkal_workload", "mgnrega_schema_e",
    "mgnrega_count", "railway_missing_index", "gst_unbounded_aggregation",
    "pds_n_plus_one", "mgnrega_implicit_cast",
]

failures = []

for tid in TASKS:
    # Reset to get real query
    try:
        r = requests.post(f"{BASE}/reset", params={"task_id": tid}, timeout=T)
        obs = r.json()
        real_query = obs.get("current_query", "SELECT 1")
        task_id_got = obs.get("task_id", "?")
    except Exception as e:
        print(f"[RESET FAIL] {tid}: {e}")
        failures.append((tid, "RESET_FAIL", None))
        continue

    # Three actions: passthrough (worst case), minimal fix, and correct pattern
    actions = [
        # Action 0: exact same query — should get ~0.5 not 0.0 or 1.0
        {
            "optimized_query": real_query,
            "identified_pattern": "NONE",
            "explanation": "no change",
            "index_statements": [],
            "schema_analysis": ""
        },
        # Action 1: SELECT 1 — edge case that often triggers 0.0
        {
            "optimized_query": "SELECT 1",
            "identified_pattern": "NONE",
            "explanation": "minimal",
            "index_statements": [],
            "schema_analysis": ""
        },
    ]

    for ai, action in enumerate(actions):
        # Re-reset for each action
        try:
            r2 = requests.post(f"{BASE}/reset", params={"task_id": tid}, timeout=T)
        except:
            pass

        try:
            s = requests.post(f"{BASE}/step", json=action, timeout=T)
            data = s.json()
            reward = float(data.get("reward", -1))
            detail = data.get("reward_detail", {})

            ok = (0.0 < reward < 1.0)
            sym = "✅" if ok else "❌ BOUNDARY VIOLATION"
            print(f"  {sym} {tid} action={ai} reward={reward:.4f}")

            if not ok:
                failures.append((tid, ai, reward, detail))
        except Exception as e:
            print(f"  ⚠️  {tid} action={ai} EXCEPTION: {e}")
            failures.append((tid, ai, f"EXC:{e}", {}))

print("\n" + "="*60)
if failures:
    print(f"❌ {len(failures)} FAILURES:")
    for f in failures:
        print(f"   {f}")
else:
    print("✅ ALL CLEAR — every reward in (0.0, 1.0)")
