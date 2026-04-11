# server/environment.py

import random
import re
import sqlite3
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

PROD_ROWS = 5_000_000
LOCAL_ROWS = max(SEED_ROWS, 1)

PATTERN_SLOW_FACTOR = {
    "SELECT_STAR":           120.0,
    "N_PLUS_ONE":            200.0,
    "CARTESIAN_PRODUCT":     500.0,
    "MISSING_INDEX":          80.0,
    "LEADING_WILDCARD":       90.0,
    "IMPLICIT_CAST":          70.0,
    "UNBOUNDED_AGGREGATION":  60.0,
    "NONE":                   50.0,
}

PATTERN_FAST_FACTOR = {
    "SELECT_STAR":            8.0,
    "N_PLUS_ONE":             5.0,
    "CARTESIAN_PRODUCT":      6.0,
    "MISSING_INDEX":          3.0,
    "LEADING_WILDCARD":       6.0,
    "IMPLICIT_CAST":          4.0,
    "UNBOUNDED_AGGREGATION": 10.0,
    "NONE":                  10.0,
}


def _display_time(raw_ms: float, scale_factor: float) -> float:
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

        # ✅ Only seed if DB doesn't exist or is empty — never re-seed
        if not self._db_path.exists() or self._db_path.stat().st_size < 100_000:
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

        done = (
            self._state.current_step >= self._state.max_steps
            or reward_detail.total >= {1: 0.70, 2: 0.70, 3: 0.58, 4: 0.45, 5: 0.35}.get(
                self._state.curriculum_level, 0.70
            )
        )

        self._state.episode_rewards.append(reward_detail.total)

        if done:
            self._state.is_running = False
            best_reward = max(self._state.episode_rewards)
            self.curriculum.record_episode(best_reward)

        pattern = task.expected_pattern
        orig_is_scan = task.original_plan and (task.original_plan.using_index is None)
        opt_uses_index = opt_plan and opt_plan.using_index is not None

        if opt_uses_index and orig_is_scan:
            opt_scale = PATTERN_FAST_FACTOR.get(pattern, 8.0)
        elif reward_detail.speedup_ratio >= 2.0:
            opt_scale = PATTERN_FAST_FACTOR.get(pattern, 8.0)
        else:
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

        # ✅ Always strictly between 0 and 1
        final_reward = round(max(0.01, min(0.99, float(reward_detail.total))), 4)

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
    # QUERY EXECUTION — ✅ FAST: direct disk, 3 runs only
    # ─────────────────────────────────────────
    def _run_query(self, query: str, index_stmts: list = None):
        """
        Run query directly on disk DB (no full memory copy).
        3 runs for timing stability. Much faster than previous 9-run memory copy.
        """
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA cache_size = -8000")

        # Apply indexes in a temp in-memory overlay only if needed
        if index_stmts:
            # For index testing, use memory copy but only once
            disk_conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
            conn = sqlite3.connect(":memory:")
            disk_conn.backup(conn)
            disk_conn.close()
            for stmt in index_stmts:
                stmt = stmt.strip()
                if stmt.upper().startswith("CREATE"):
                    try:
                        conn.execute(stmt)
                        conn.commit()
                    except Exception:
                        pass

        # Execution plan
        try:
            plan_rows = conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
            plan_text = " | ".join(str(r) for r in plan_rows)
        except Exception:
            plan_text = ""

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

        # ✅ Only 3 runs (was 9) — much faster
        times = []
        rows = []
        for i in range(3):
            start = time.perf_counter()
            try:
                rows = conn.execute(query).fetchall()
            except Exception as e:
                conn.close()
                raise e
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        elapsed_ms = sorted(times)[1] if len(times) >= 3 else times[0]  # median of 3
        elapsed_ms = max(elapsed_ms, 0.001)

        exec_plan.rows_returned = len(rows)

        try:
            tbl_name = query.strip().upper().split("FROM")[1].split()[0].strip(";, ")
            examined = conn.execute(f"SELECT COUNT(*) FROM {tbl_name}").fetchone()[0]
        except Exception:
            examined = len(rows) * 10

        exec_plan.rows_examined = examined if is_full_scan else len(rows)
        exec_plan.cost_estimate = round(exec_plan.rows_examined * 0.001, 4)

        conn.close()
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