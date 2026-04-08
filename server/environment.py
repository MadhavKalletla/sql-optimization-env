# server/environment.py

import random
import re
import sqlite3
import statistics
import time
import uuid
from pathlib import Path
from typing import Optional

from .models import (
    SQLOptObservation, SQLOptAction, StepResult,
    EnvironmentState, ExecutionPlan, SQLOptReward,
)
from .reward import RewardComposer
from .hack_detector import HackDetector
from tasks.task_registry import TaskRegistry
from curriculum.curriculum_engine import CurriculumEngine
from data.seed_database import seed_database


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "fixtures" / "benchmark_seed42.db"
SEED_ROWS = 50_000

# Scale factor: simulates what timing would look like on a 5M-row production DB.
# SQLite on 50k rows is ~100x faster than production.  We apply this factor
# ONLY to the displayed execution_time_ms so the UI looks realistic.
# Grading still uses raw timings so ratio comparisons remain valid.
SCALE_FACTOR = 80.0


class SQLOptEnvironment:

    def __init__(self):
        self.task_registry = TaskRegistry()
        self.curriculum = CurriculumEngine()
        self.reward_composer = RewardComposer()
        self.hack_detector = HackDetector()
        self._state: Optional[EnvironmentState] = None
        self._current_task = None
        self._db_path = DB_PATH

        # Seed only if DB does not exist
        if not self._db_path.exists():
            try:
                print(f"🚀 Seeding database ({SEED_ROWS} rows)…", flush=True)
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                seed_database(str(self._db_path), SEED_ROWS)
                print("✅ Database seeded successfully", flush=True)
            except Exception as e:
                print(f"❌ Seeding failed: {e}", flush=True)
        else:
            print("✅ Database already exists — reusing", flush=True)

    # ─────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────
    def reset(self, task_id: str = None) -> SQLOptObservation:
        current_level = self.curriculum.current_level

        if task_id:
            task = self.task_registry.get_task_by_id(task_id)
            if task is None:
                raise ValueError(f"Task '{task_id}' not found")

            # ── CURRICULUM GATE ──────────────────────────────────────────
            # Do NOT allow the agent to jump to a level above their current
            # earned curriculum level.  Silently fall back to best matching
            # task at or below current level.
            if task.curriculum_level > current_level:
                print(
                    f"[CURRICULUM] Blocked jump to level {task.curriculum_level} "
                    f"(current={current_level}). Falling back to level {current_level}.",
                    flush=True,
                )
                task = self.task_registry.get_task_for_level(current_level)
        else:
            task = self.task_registry.get_task_for_level(current_level)

        self._current_task = task
        level = self.curriculum.current_level  # always authoritative from engine

        self._state = EnvironmentState(
            episode_id=str(uuid.uuid4())[:8],
            current_task_id=task.task_id,
            current_step=0,
            max_steps=task.max_steps,
            curriculum_level=level,
            episode_rewards=[],
            total_episodes=self.curriculum.total_episodes,
            is_running=True,
        )

        raw_time, orig_rows, exec_plan = self._run_query(task.slow_query)
        task.original_time_ms = raw_time
        task.original_plan = exec_plan

        # Scale for realistic display
        display_time = round(raw_time * SCALE_FACTOR, 2)

        return SQLOptObservation(
            task_id=task.task_id,
            step_number=0,
            goal=task.goal,
            schema_ddl=task.schema_ddl,
            current_query=task.slow_query,
            execution_plan=exec_plan,
            execution_time_ms=display_time,
            row_count=orig_rows,
            db_stats=self._get_db_stats(task.tables),
            curriculum_level=level,
            anti_pattern_hint=task.hint if level <= 2 else None,
        )

    # ─────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────
    def step(self, action: SQLOptAction) -> StepResult:
        if not self._state or not self._state.is_running:
            raise ValueError("Call reset() first")

        self._state.current_step += 1
        task = self._current_task

        hack = self.hack_detector.detect(action, task)

        query_error = None
        try:
            opt_time, opt_rows, opt_plan = self._run_query(
                action.optimized_query, action.index_statements
            )
        except Exception as e:
            # Syntax error — use a very slow time (penalizes speedup) but
            # do NOT end the episode; let the agent fix and retry.
            opt_time = task.original_time_ms * 3.0
            opt_rows = 0
            opt_plan = None
            query_error = str(e)

        reward_detail = self.reward_composer.compute(
            task=task,
            action=action,
            orig_time=task.original_time_ms,
            opt_time=opt_time,
            opt_rows=opt_rows,
            opt_plan=opt_plan,
            hack=hack,
            query_error=query_error,
            db_path=self._db_path,
        )

        # Episode ends on max_steps OR excellent reward — NOT on syntax error
        # (agent should get a chance to fix their query)
        done = (
            self._state.current_step >= self._state.max_steps
            or reward_detail.total >= 0.95
        )

        self._state.episode_rewards.append(reward_detail.total)

        if done:
            self._state.is_running = False
            best_reward = max(self._state.episode_rewards)
            self.curriculum.record_episode(best_reward)

        # Scale optimized time for display too
        display_opt_time = round(opt_time * SCALE_FACTOR, 2)

        next_obs = SQLOptObservation(
            task_id=task.task_id,
            step_number=self._state.current_step,
            goal=task.goal,
            schema_ddl=task.schema_ddl,
            current_query=action.optimized_query,
            execution_plan=opt_plan if opt_plan else task.original_plan,
            execution_time_ms=display_opt_time,
            row_count=opt_rows,
            db_stats=self._get_db_stats(task.tables),
            curriculum_level=self._state.curriculum_level,
            error_message=query_error,
        )

        return StepResult(
            observation=next_obs,
            reward=reward_detail.total,
            reward_detail=reward_detail,
            done=done,
            info={"hack": hack, "query_error": query_error},
        )

    # ─────────────────────────────────────────
    # STATE
    # ─────────────────────────────────────────
    def state(self) -> EnvironmentState:
        if self._state:
            return self._state

        return EnvironmentState(
            episode_id="init",
            current_task_id="none",
            current_step=0,
            max_steps=3,
            curriculum_level=self.curriculum.current_level,
            episode_rewards=[],
            total_episodes=self.curriculum.total_episodes,
            is_running=False,
        )

    # ─────────────────────────────────────────
    # QUERY EXECUTION  (stable, realistic timing)
    # ─────────────────────────────────────────
    def _run_query(self, query: str, index_stmts: list = None):
        """
        Copy the on-disk DB to an in-memory DB for each execution so indexes
        applied here do not affect subsequent runs.  Run the statement multiple
        times and take the median to get a stable timing signal.
        """
        disk_conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
        mem_conn = sqlite3.connect(":memory:")
        disk_conn.backup(mem_conn)
        disk_conn.close()

        mem_conn.execute("PRAGMA foreign_keys = ON")
        mem_conn.execute("PRAGMA cache_size = -8000")   # 8 MB cache — realistic

        if index_stmts:
            for stmt in index_stmts:
                stmt = stmt.strip()
                if not stmt.upper().startswith("CREATE"):
                    continue
                try:
                    mem_conn.execute(stmt)
                    mem_conn.commit()
                except Exception:
                    pass

        # Execution plan
        plan_rows = mem_conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
        plan_text = " | ".join(str(r) for r in plan_rows)

        using_index = "USING INDEX" in plan_text.upper() or "SEARCH" in plan_text.upper()
        is_full_scan = "SCAN" in plan_text.upper() and not using_index

        # Count rows examined from plan detail
        rows_examined_est = self._estimate_rows_examined(plan_text, query)

        exec_plan = ExecutionPlan(
            operation="FULL TABLE SCAN" if is_full_scan else "INDEX SCAN",
            rows_examined=rows_examined_est,
            rows_returned=0,          # filled after execution
            cost_estimate=round(rows_examined_est * 0.001, 4),
            using_index=plan_text if using_index else None,
            missing_index_hint="Consider adding index" if is_full_scan else None,
            explain_raw=plan_text,
        )

        # Warm up + multiple samples for stable timing
        SAMPLES = 7
        times = []
        rows = []
        for i in range(SAMPLES):
            start = time.perf_counter()
            rows = mem_conn.execute(query).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
            if i > 0:    # discard first (cold cache) for fair comparison
                times.append(elapsed)

        elapsed_ms = statistics.median(times) if times else 0.001
        elapsed_ms = max(elapsed_ms, 0.001)

        exec_plan.rows_returned = len(rows)
        exec_plan.rows_examined = max(exec_plan.rows_examined, len(rows))

        mem_conn.close()
        return elapsed_ms, len(rows), exec_plan

    def _estimate_rows_examined(self, plan_text: str, query: str) -> int:
        """Extract a plausible rows-examined estimate from EXPLAIN QUERY PLAN output."""
        # Try to extract anything numeric from plan text
        numbers = re.findall(r'\b(\d+)\b', plan_text)
        if numbers:
            return max(int(n) for n in numbers)
        # Fallback: count columns in SELECT to get rough cost estimate
        return 0

    # ─────────────────────────────────────────
    # DB STATS
    # ─────────────────────────────────────────
    def _get_db_stats(self, tables: list) -> dict:
        conn = sqlite3.connect(str(self._db_path))
        stats = {}
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = {"row_count": count}
            except Exception as e:
                stats[table] = {"error": str(e)}
        conn.close()
        return stats