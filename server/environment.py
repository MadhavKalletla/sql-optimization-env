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
SEED_ROWS = 200_000

# ─────────────────────────────────────────────────────────────────────────────
# REALISTIC TIMING SIMULATION
#
# SQLite in-memory on 50 k rows is fast.  We apply a pattern-aware scale so
# the displayed timing looks like a production DB with ~5 M rows.
#
# For slow (anti-pattern) queries we apply a HIGH multiplier.
# For optimized queries the multiplier shrinks based on plan quality — giving
# the agent a visible, meaningful speedup in the UI.
# ─────────────────────────────────────────────────────────────────────────────
PROD_ROWS = 5_000_000
LOCAL_ROWS = max(SEED_ROWS, 1)

# Anti-pattern → extra overhead relative to a clean query at production scale
PATTERN_SLOW_FACTOR = {
    "SELECT_STAR":           120.0,   # all columns fetched → huge I/O
    "N_PLUS_ONE":            200.0,   # per-row correlated subquery
    "CARTESIAN_PRODUCT":     500.0,   # cross join explodes
    "MISSING_INDEX":          80.0,   # full table scan
    "LEADING_WILDCARD":       90.0,   # full scan due to prefix %
    "IMPLICIT_CAST":          70.0,   # cast prevents index use
    "UNBOUNDED_AGGREGATION":  60.0,   # no predicate → aggregate all
    "NONE":                   50.0,
}

# Factor applied to the OPTIMIZED query (much lower)
PATTERN_FAST_FACTOR = {
    "SELECT_STAR":            8.0,    # column projection only → fast
    "N_PLUS_ONE":             5.0,    # single join
    "CARTESIAN_PRODUCT":      6.0,    # proper join condition
    "MISSING_INDEX":          3.0,    # index scan
    "LEADING_WILDCARD":       6.0,    # prefix known → smaller scan
    "IMPLICIT_CAST":          4.0,    # no cast → index used
    "UNBOUNDED_AGGREGATION": 10.0,    # date filter → partial scan
    "NONE":                  10.0,
}


def _display_time(raw_ms: float, scale_factor: float) -> float:
    """Scale raw SQLite timing to a production-realistic value."""
    return round(max(raw_ms * scale_factor, 0.5), 2)


class SQLOptEnvironment:

    def __init__(self):
        self.task_registry = TaskRegistry()
        self.curriculum = CurriculumEngine()
        self.reward_composer = RewardComposer()
        self.hack_detector = HackDetector()
        self._state: Optional[EnvironmentState] = None
        self._current_task = None
        self._db_path = DB_PATH

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
            # Allow explicit task_id to bypass curriculum gate for evaluation
            # (curriculum still applies for random task selection)
        else:
            exclude_id = self._current_task.task_id if self._current_task else None
            task = self.task_registry.get_task_for_level(current_level, exclude_task_id=exclude_id)

        self._current_task = task
        level = self.curriculum.current_level

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

        # Apply pattern-aware SLOW scale for realistic display
        slow_scale = PATTERN_SLOW_FACTOR.get(task.expected_pattern, 80.0)
        display_time = _display_time(raw_time, slow_scale)

        exec_plan.rows_examined = max(exec_plan.rows_examined, orig_rows)

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
            orig_plan=task.original_plan,
            opt_plan=opt_plan,
            hack=hack,
            query_error=query_error,
            db_path=self._db_path,
        )

        # Episode ends on max_steps OR score >= 0.70 (frontend pass threshold is 0.70)
        done = (
            self._state.current_step >= self._state.max_steps
            or reward_detail.total >= {1: 0.70, 2: 0.70, 3: 0.58, 4: 0.45, 5: 0.35}.get(self._state.curriculum_level, 0.70)
        )

        self._state.episode_rewards.append(reward_detail.total)

        if done:
            self._state.is_running = False
            best_reward = max(self._state.episode_rewards)
            self.curriculum.record_episode(best_reward)

        # Scale optimized time: use FAST scale if the plan looks better than original
        pattern = task.expected_pattern
        orig_is_scan = task.original_plan and (task.original_plan.using_index is None)
        opt_uses_index = opt_plan and opt_plan.using_index is not None

        if opt_uses_index and orig_is_scan:
            # Clearly improved: show big time reduction
            opt_scale = PATTERN_FAST_FACTOR.get(pattern, 8.0)
        elif reward_detail.speedup_ratio >= 2.0:
            opt_scale = PATTERN_FAST_FACTOR.get(pattern, 8.0)
        else:
            # Marginal improvement or no change: scale similarly to slow
            opt_scale = PATTERN_SLOW_FACTOR.get(pattern, 80.0) * 0.85

        display_opt_time = _display_time(opt_time, opt_scale)

        if opt_plan:
            opt_plan.rows_examined = max(opt_plan.rows_examined, opt_rows)

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

        # Final safety clamp — guarantee reward is strictly in (0, 1) at API level
        # Use 0.002/0.998 bounds (not 0.001/0.999) — round(0.999,N) can equal 1.0 in Python!
        final_reward = round(max(0.002, min(0.998, float(reward_detail.total))), 4)

        return StepResult(
            observation=next_obs,
            reward=final_reward,
            reward_detail=reward_detail,
            done=done,
            info={"hack": hack, "query_error": query_error},
        )

    # ─────────────────────────────────────────
    # STATE
    # ─────────────────────────────────────────
    def state(self) -> EnvironmentState:
        if self._state:
            self._state.recent_scores = self.curriculum.recent_scores[-10:]
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
            recent_scores=self.curriculum.recent_scores[-10:],
        )

    # ─────────────────────────────────────────
    # QUERY EXECUTION — stable median timing
    # ─────────────────────────────────────────
    def _run_query(self, query: str, index_stmts: list = None):
        """
        Copy disk DB → in-memory, apply indexes, execute query multiple
        times for stable median timing, return (median_ms, row_count, plan).
        """
        disk_conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
        mem_conn = sqlite3.connect(":memory:")
        disk_conn.backup(mem_conn)
        disk_conn.close()

        mem_conn.execute("PRAGMA foreign_keys = ON")
        mem_conn.execute("PRAGMA cache_size = -16000")   # 16 MB cache

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

        using_index = ("USING INDEX" in plan_text.upper() or
                       ("SEARCH" in plan_text.upper() and "SCAN" not in plan_text.upper()))
        is_full_scan = "SCAN" in plan_text.upper() and not using_index

        exec_plan = ExecutionPlan(
            operation="FULL TABLE SCAN" if is_full_scan else "INDEX SCAN",
            rows_examined=0,
            rows_returned=0,
            cost_estimate=0.0,
            using_index=plan_text if using_index else None,
            missing_index_hint="Consider adding an index" if is_full_scan else None,
            explain_raw=plan_text,
        )

        # Run 9 times; discard first 2 (cold cache); median of remaining 7
        RUNS = 9
        times = []
        rows = []
        for i in range(RUNS):
            start = time.perf_counter()
            rows = mem_conn.execute(query).fetchall()
            elapsed = (time.perf_counter() - start) * 1000
            if i >= 2:
                times.append(elapsed)

        elapsed_ms = statistics.median(times) if times else 0.001
        elapsed_ms = max(elapsed_ms, 0.001)

        exec_plan.rows_returned = len(rows)
        # Rows examined estimated from plan text — SCAN means full table, SEARCH means indexed
        if "SCAN" in plan_text.upper() and "SEARCH" not in plan_text.upper():
            # Full scan: examined ≈ total table rows (approximate from db stats)
            try:
                tbl_name = query.strip().upper().split("FROM")[1].split()[0].strip(";, ")
                examined = mem_conn.execute(
                    f"SELECT COUNT(*) FROM {tbl_name}"
                ).fetchone()[0]
            except Exception:
                examined = len(rows) * 100  # fallback estimate
        else:
            examined = len(rows)  # index scan: examined ≈ returned
        exec_plan.rows_examined = examined
        exec_plan.cost_estimate = round(examined * 0.001, 4)

        mem_conn.close()
        return elapsed_ms, len(rows), exec_plan

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