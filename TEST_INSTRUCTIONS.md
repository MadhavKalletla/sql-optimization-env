# Live Endpoint Testing Instructions

## Your HuggingFace Space is Currently Not Responding

**URL:** https://kalletlamadhav-sql-optimized-env-new.hf.space

All curl/HTTP requests are timing out after 30 seconds. This indicates the Space is either:
- 😴 **Sleeping** (free tier Spaces sleep after inactivity)
- 🔨 **Building** (still deploying your latest changes)
- 💥 **Crashed** (runtime error preventing startup)
- ❓ **Wrong URL** (Space name might be different)

## STEP 1: Wake Up Your Space

1. **Visit the Space URL in your browser:**
   ```
   https://kalletlamadhav-sql-optimized-env-new.hf.space
   ```

2. **Check the Space status page:**
   ```
   https://huggingface.co/spaces/kalletlamadhav/sql-optimized-env-new
   ```
   - Look for "Building", "Running", or "Runtime error" status
   - Check the logs for any error messages

3. **Wait 30-60 seconds** for the Space to fully wake up

## STEP 2: Test Endpoints Using curl

Once the Space is accessible, run these commands:

### Test 1: Health Check
```bash
curl -s https://kalletlamadhav-sql-optimized-env-new.hf.space/health | python -m json.tool
```

**Expected:** JSON with `"status": "ok"`

### Test 2: List Tasks
```bash
curl -s https://kalletlamadhav-sql-optimized-env-new.hf.space/tasks | python -m json.tool
```

**Expected:** Array with 3+ task objects

### Test 3: Reset Environment
```bash
curl -s -X POST "https://kalletlamadhav-sql-optimized-env-new.hf.space/reset?task_id=gst_missing_index" | python -m json.tool
```

**Expected:** Observation object with fields:
- `task_id`: "gst_missing_index"
- `step_number`: 0
- `goal`: string
- `schema_ddl`: string
- `slow_query`: string
- `expected_pattern`: string

### Test 4: Get State
```bash
curl -s https://kalletlamadhav-sql-optimized-env-new.hf.space/state | python -m json.tool
```

**Expected:** State object with `current_task_id` and `episode_count`

### Test 5: Submit Step (CRITICAL - Reward Validation)
```bash
curl -s -X POST "https://kalletlamadhav-sql-optimized-env-new.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{
    "optimized_query": "SELECT gstin_supplier, invoice_date FROM gst_invoice_records WHERE invoice_date >= '\''2025-01-01'\''",
    "identified_pattern": "MISSING_INDEX",
    "explanation": "Added index on invoice_date to avoid full table scan",
    "index_statements": ["CREATE INDEX idx_invoice_date ON gst_invoice_records(invoice_date)"],
    "schema_analysis": "No index on invoice_date"
  }' | python -m json.tool
```

**Expected:** Step result with:
- `reward`: **MUST be strictly between 0.01 and 0.99** (NOT 0.0, NOT 1.0)
- `done`: boolean
- `observation`: object with task details

## STEP 3: Verify Reward Values

**CRITICAL CHECK:** The `reward` field (or `reward.total` if it's an object) must be:
- ✅ Greater than 0.01
- ✅ Less than 0.99
- ❌ NOT exactly 0.0
- ❌ NOT exactly 1.0

### Example Valid Responses:
```json
{
  "reward": 0.45,  // ✅ VALID
  "done": false,
  "observation": {...}
}
```

```json
{
  "reward": {
    "total": 0.67,  // ✅ VALID
    "speedup_score": 0.25,
    ...
  },
  "done": false,
  "observation": {...}
}
```

### Example INVALID Responses:
```json
{
  "reward": 0.0,  // ❌ FAIL - exactly 0.0
  ...
}
```

```json
{
  "reward": 1.0,  // ❌ FAIL - exactly 1.0
  ...
}
```

## STEP 4: If Tests Fail

### If /health times out or returns error:
- Space is not running properly
- Check HuggingFace Space logs
- Verify Dockerfile and requirements are correct

### If /tasks returns empty array:
- Check `tasks/` directory has task files
- Verify `task_registry.py` is loading tasks correctly

### If /reset returns error or empty:
- Check `server/main.py` reset endpoint
- Verify `server/environment.py` reset method

### If /step reward is 0.0 or 1.0:
- **This is the main Phase 2 validation issue**
- All graders must clamp scores to (0.01, 0.99)
- Check files already fixed in this repo

## All Fixes Already Applied

The following files have been fixed to ensure rewards are strictly between 0.01 and 0.99:

✅ `server/graders/speedup_grader.py`
✅ `server/graders/equivalence_grader.py`
✅ `server/graders/antipattern_grader.py`
✅ `server/graders/index_grader.py`
✅ `server/reward.py`
✅ `server/app.py`
✅ `pyproject.toml`

**If your Space is using old code**, you need to:
1. Push the fixed files to your HuggingFace Space repository
2. Wait for the Space to rebuild
3. Test again

## Quick Python Test Script

If curl is not available, use this Python script:

```python
import requests
import json

BASE_URL = "https://kalletlamadhav-sql-optimized-env-new.hf.space"

# Test health
print("Testing /health...")
r = requests.get(f"{BASE_URL}/health", timeout=10)
print(json.dumps(r.json(), indent=2))

# Test reset
print("\nTesting /reset...")
r = requests.post(f"{BASE_URL}/reset?task_id=gst_missing_index", timeout=10)
print(json.dumps(r.json(), indent=2))

# Test step
print("\nTesting /step...")
action = {
    "optimized_query": "SELECT gstin_supplier FROM gst_invoice_records WHERE invoice_date >= '2025-01-01'",
    "identified_pattern": "MISSING_INDEX",
    "explanation": "Added index",
    "index_statements": ["CREATE INDEX idx_date ON gst_invoice_records(invoice_date)"],
    "schema_analysis": "No index"
}
r = requests.post(f"{BASE_URL}/step", json=action, timeout=10)
result = r.json()
print(json.dumps(result, indent=2))

# Validate reward
reward = result.get("reward")
if isinstance(reward, dict):
    reward = reward.get("total", 0)

print(f"\n{'='*50}")
if 0.01 < reward < 0.99:
    print(f"✅ PASS: Reward {reward} is valid!")
else:
    print(f"❌ FAIL: Reward {reward} is NOT in (0.01, 0.99)")
print(f"{'='*50}")
```

## Summary

Your local code has been fixed and is ready for Phase 2 validation. The issue is that your HuggingFace Space is not responding to HTTP requests. You need to:

1. ✅ Visit the Space URL to wake it up
2. ✅ Verify it's running (not building/crashed)
3. ✅ Push the fixed code if Space is using old version
4. ✅ Run the tests above to verify all endpoints work
5. ✅ Confirm reward values are strictly between 0.01 and 0.99
