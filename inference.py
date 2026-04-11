#!/usr/bin/env python3
"""
inference.py — OpenEnv benchmark inference script.
ALL scores strictly in (0.011, 0.989) — never exactly 0.0 or 1.0.
"""

import json, os, sys, time
from typing import List
import requests
from openai import OpenAI

# ── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://api.openai.com/v1')
MODEL_NAME   = os.environ.get('MODEL_NAME', 'gpt-4o-mini')
HF_TOKEN     = os.environ.get('HF_TOKEN', '')
API_KEY      = HF_TOKEN if HF_TOKEN else os.environ.get('OPENAI_API_KEY', 'placeholder-key')
ENV_BASE_URL = os.environ.get('ENV_URL', 'http://localhost:7860')

TEMPERATURE       = 0.0
MAX_TOKENS        = 1024
MAX_STEPS         = 3
SUCCESS_THRESHOLD = 0.7

BENCHMARK_TASKS = [
    "gst_missing_index",
    "gst_n_plus_one",
    "gst_multi_join",
    "pds_select_star",
    "railway_simple_filter",
    "pds_cartesian",
    "mgnrega_wildcard",
    "railway_tatkal_workload",
    "mgnrega_schema_e",
]

SYSTEM_PROMPT = """You are an expert SQL database engineer.
You will be given a slow SQL query, its schema, and execution plan.
Your job is to:
1. Identify the anti-pattern type causing the slowness
2. Explain why the query is slow
3. Rewrite the query to be faster
4. Add appropriate CREATE INDEX statements
Respond ONLY in valid JSON with this exact structure:
{
  "optimized_query": "SELECT ...",
  "identified_pattern": "MISSING_INDEX",
  "explanation": "The query does a full table scan because...",
  "index_statements": ["CREATE INDEX idx_name ON table(col)"],
  "schema_analysis": "Table has 5 columns, no indexes on..."
}
identified_pattern must be one of: N_PLUS_ONE, CARTESIAN_PRODUCT, MISSING_INDEX,
SELECT_STAR, LEADING_WILDCARD, IMPLICIT_CAST, UNBOUNDED_AGGREGATION, NONE"""


# ── Safe clamp — NEVER returns exactly 0.0 or 1.0 ───────────────────────────
def _safe(v: float) -> float:
    return round(max(0.011, min(0.989, float(v))), 4)


# ── Logging ─────────────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str):
    print("[START]", json.dumps({
        "task":      task,
        "env":       env,
        "model":     model,
        "timestamp": time.time(),
    }), flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error=None):
    print("[STEP]", json.dumps({
        "step":   step,
        "action": action[:200] if action else "",
        "reward": _safe(reward),
        "done":   done,
        "error":  str(error) if error else None,
    }), flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    print("[END]", json.dumps({
        "success": success,
        "steps":   steps,
        "score":   _safe(score),
        "rewards": [_safe(r) for r in rewards],
    }), flush=True)


# ── Prompt builder ───────────────────────────────────────────────────────────

def build_user_prompt(obs: dict) -> str:
    return f"""
TASK: {obs.get('goal', '')}
SCHEMA:
{obs.get('schema_ddl', '')[:500]}
CURRENT QUERY (SLOW):
{obs.get('current_query', '')}
EXECUTION PLAN:
{json.dumps(obs.get('execution_plan', {}), indent=2)}
EXECUTION TIME: {obs.get('execution_time_ms', 0):.0f}ms
DB STATS: {json.dumps(obs.get('db_stats', {}))}
Optimize this query. Respond in JSON only."""


# ── Model call ───────────────────────────────────────────────────────────────

def get_model_action(client: OpenAI, obs: dict) -> dict:
    prompt = build_user_prompt(obs)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        raw = (completion.choices[0].message.content or "").strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[DEBUG] Model error: {e}", flush=True)
        return {
            "optimized_query":    obs.get("current_query", "SELECT 1"),
            "identified_pattern": "NONE",
            "explanation":        f"Fallback: {e}",
            "index_statements":   [],
            "schema_analysis":    "",
        }


# ── Task runner ──────────────────────────────────────────────────────────────

def run_task(client: OpenAI, task_id: str) -> float:
    log_start(task=task_id, env="sql-optimization-env", model=MODEL_NAME)

    rewards     = []
    steps_taken = 0

    # ── Reset ────────────────────────────────────────────────────────────────
    try:
        resp = requests.get(
            f"{ENV_BASE_URL}/reset",
            params={"task_id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"[ERROR] Reset failed for {task_id}: {e}", flush=True)
        log_end(success=False, steps=0, score=0.011, rewards=[0.011])
        return 0.011

    done = False

    # ── Steps ────────────────────────────────────────────────────────────────
    for step in range(1, MAX_STEPS + 1):
        if done:
            break

        action_dict = get_model_action(client, obs)

        try:
            step_resp = requests.post(
                f"{ENV_BASE_URL}/step",
                json=action_dict,
                timeout=60,
            )
            step_resp.raise_for_status()
            result = step_resp.json()
        except Exception as e:
            log_step(step, "", 0.011, True, error=str(e))
            steps_taken = step
            break

        # Clamp reward from server BEFORE logging or appending
        reward = _safe(float(result.get("reward", 0.011)))
        done   = bool(result.get("done", False))
        obs    = result.get("observation", obs)

        rewards.append(reward)
        steps_taken = step

        log_step(
            step=step,
            action=action_dict.get("optimized_query", ""),
            reward=reward,
            done=done,
        )

        if done:
            break

    # ── Score ─────────────────────────────────────────────────────────────────
    score   = sum(rewards) / len(rewards) if rewards else 0.011
    score   = _safe(score)
    success = score >= SUCCESS_THRESHOLD

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        client = OpenAI(
            base_url=API_BASE_URL or "https://api.openai.com/v1",
            api_key=API_KEY or "placeholder-key",
        )
    except Exception as e:
        print(f"[FATAL] OpenAI client init failed: {e}", flush=True)
        sys.exit(1)

    print("[DEBUG] Starting SQL Optimization Benchmark", flush=True)
    print(f"[DEBUG] Model: {MODEL_NAME}",      flush=True)
    print(f"[DEBUG] Env URL: {ENV_BASE_URL}",  flush=True)
    print(f"[DEBUG] Tasks: {BENCHMARK_TASKS}", flush=True)

    all_scores = {}

    for task_id in BENCHMARK_TASKS:
        print(f"\n[DEBUG] Running task: {task_id}", flush=True)
        score = run_task(client, task_id)
        all_scores[task_id] = score
        print(f"[DEBUG] Task {task_id} score: {score:.4f}", flush=True)

    # Final safety clamp on every score before printing
    all_scores = {k: _safe(v) for k, v in all_scores.items()}
    avg = _safe(sum(all_scores.values()) / len(all_scores)) if all_scores else 0.011

    print(json.dumps({
        "event":   "BENCHMARK_COMPLETE",
        "scores":  {k: v for k, v in all_scores.items()},
        "average": avg,
    }), flush=True)


if __name__ == "__main__":
    main()