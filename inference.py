#!/usr/bin/env python3
"""
inference.py — OpenEnv benchmark inference script.
Fully corrected for:
- Proper logging format
- Safe JSON parsing
- HTTP error handling
- Timeout protection
- Robust fallback handling
"""

import json, os, sys, time
from typing import List
from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN")
LOCAL_IMAGE_NAME = os.environ.get("LOCAL_IMAGE_NAME")
API_KEY = HF_TOKEN or ""
ENV_BASE_URL = os.environ.get("ENV_URL", "http://localhost:7860")

TEMPERATURE = 0.0
MAX_TOKENS = 1024
MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.7

BENCHMARK_TASKS = [
    "gst_missing_index",
    "gst_n_plus_one",
    "gst_multi_join",
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


# ── Logging (STRICT FORMAT) ──────────────────────────────────────────────

def log_start(task: str, env: str, model: str):
    print("[START]", json.dumps({
        "task": task,
        "env": env,
        "model": model,
        "timestamp": time.time(),
    }), flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error=None):
    print("[STEP]", json.dumps({
        "step": step,
        "action": action[:200] if action else "",
        "reward": round(reward, 4),
        "done": done,
        "error": str(error) if error else None,
    }), flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    print("[END]", json.dumps({
        "success": success,
        "steps": steps,
        "score": round(score, 4),
        "rewards": [round(r, 4) for r in rewards],
    }), flush=True)


# ── Prompt builder ────────────────────────────────────────────────────────

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


# ── Model call ────────────────────────────────────────────────────────────

def get_model_action(client: OpenAI, obs: dict) -> dict:
    prompt = build_user_prompt(obs)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )

        raw = (completion.choices[0].message.content or "").strip()

        # ✅ Safe JSON extraction
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) > 1:
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]

        return json.loads(raw)

    except Exception as e:
        print(f"[DEBUG] Model error: {e}", flush=True)
        return {
            "optimized_query": obs.get("current_query", ""),
            "identified_pattern": "NONE",
            "explanation": "Fallback due to parsing/model error",
            "index_statements": [],
            "schema_analysis": "",
        }


# ── Task runner ───────────────────────────────────────────────────────────

def run_task(client: OpenAI, task_id: str) -> float:
    import requests

    log_start(task=task_id, env="sql-optimization-env", model=MODEL_NAME)

    rewards = []
    steps_taken = 0

    try:
        resp = requests.get(
            f"{ENV_BASE_URL}/reset",
            params={"task_id": task_id},
            timeout=30
        )
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"[ERROR] Reset failed: {e}", flush=True)
        return 0.0

    done = False

    for step in range(1, MAX_STEPS + 1):
        if done:
            break

        action_dict = get_model_action(client, obs)

        try:
            step_resp = requests.post(
                f"{ENV_BASE_URL}/step",
                json=action_dict,
                timeout=30
            )
            step_resp.raise_for_status()
            result = step_resp.json()
        except Exception as e:
            log_step(step, "", 0.0, True, error=e)
            break

        reward = result.get("reward", 0.0)
        done = result.get("done", False)
        obs = result.get("observation", obs)

        rewards.append(reward)
        steps_taken = step

        log_step(
            step=step,
            action=action_dict.get("optimized_query", ""),
            reward=reward,
            done=done,
        )

    score = sum(rewards) / len(rewards) if rewards else 0.0
    score = max(0.0, min(1.0, score))

    success = score >= SUCCESS_THRESHOLD

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    print("[DEBUG] Starting SQL Optimization Benchmark", flush=True)
    print(f"[DEBUG] Model: {MODEL_NAME}", flush=True)
    print(f"[DEBUG] Tasks: {BENCHMARK_TASKS}", flush=True)

    all_scores = {}

    for task_id in BENCHMARK_TASKS:
        print(f"\n[DEBUG] Running task: {task_id}", flush=True)
        score = run_task(client, task_id)
        all_scores[task_id] = score
        print(f"[DEBUG] Task {task_id} score: {score:.4f}", flush=True)

    avg = sum(all_scores.values()) / len(all_scores) if all_scores else 0.0

    print(json.dumps({
        "event": "BENCHMARK_COMPLETE",
        "scores": all_scores,
        "average": round(avg, 4),
    }), flush=True)


if __name__ == "__main__":
    main()