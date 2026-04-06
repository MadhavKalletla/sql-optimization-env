# server/environment.py

import random
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
SEED_ROWS = 50_000


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
        if task_id:
            task = self.task_registry.get_task_by_id(task_id)
            if task is None:
                raise ValueError(f"Task '{task_id}' not found")
        else:
            level = self.curriculum.current_level
            task = self.task_registry.get_task_for_level(level)

        self._current_task = task
        level = task.curriculum_level

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

        orig_time, orig_rows, exec_plan = self._run_query(task.slow_query)
        task.original_time_ms = orig_time
        task.original_plan = exec_plan

        return SQLOptObservation(
            task_id=task.task_id,
            step_number=0,
            goal=task.goal,
            schema_ddl=task.schema_ddl,
            current_query=task.slow_query,
            execution_plan=exec_plan,
            execution_time_ms=orig_time,
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

        try:
            opt_time, opt_rows, opt_plan = self._run_query(
                action.optimized_query, action.index_statements
            )
            query_error = None
        except Exception as e:
            opt_time = max(task.original_time_ms, 1.0) * 2
            opt_rows = 0   # ✅ FIX (was -1)
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

        done = (
            self._state.current_step >= self._state.max_steps
            or reward_detail.total >= 0.95
            or query_error is not None
        )

        self._state.episode_rewards.append(reward_detail.total)

        if done:
            self._state.is_running = False
            best_reward = max(self._state.episode_rewards)
            self.curriculum.record_episode(best_reward)

        next_obs = SQLOptObservation(
            task_id=task.task_id,
            step_number=self._state.current_step,
            goal=task.goal,
            schema_ddl=task.schema_ddl,
            current_query=action.optimized_query,
            execution_plan=opt_plan if opt_plan else task.original_plan,
            execution_time_ms=opt_time,
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
            info={"hack": hack},
        )

    # ─────────────────────────────────────────
    # STATE
    # ─────────────────────────────────────────
    def state(self) -> EnvironmentState:
        if not self._state:
            raise ValueError("Call reset() first")
        return self._state

    # ─────────────────────────────────────────
    # QUERY EXECUTION
    # ─────────────────────────────────────────
    def _run_query(self, query: str, index_stmts: list = None):
        disk_conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
        mem_conn = sqlite3.connect(":memory:")
        disk_conn.backup(mem_conn)
        disk_conn.close()

        mem_conn.execute("PRAGMA foreign_keys = ON")

        if index_stmts:
            for stmt in index_stmts:
                stmt = stmt.strip()
                if not stmt.upper().startswith("CREATE"):
                    continue
                try:
                    mem_conn.execute(stmt)
                except Exception:
                    pass

        plan_rows = mem_conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
        plan_text = " | ".join(str(r) for r in plan_rows)

        using_index = "USING INDEX" in plan_text.upper()
        is_full_scan = "SCAN" in plan_text.upper() and not using_index

        exec_plan = ExecutionPlan(
            operation="FULL TABLE SCAN" if is_full_scan else "INDEX SCAN",
            rows_examined=0,
            rows_returned=0,
            cost_estimate=0.0,
            using_index=plan_text if using_index else None,
            missing_index_hint="Consider adding index" if is_full_scan else None,
            explain_raw=plan_text,
        )

        start = time.perf_counter()
        rows = mem_conn.execute(query).fetchall()
        elapsed = (time.perf_counter() - start) * 1000

        mem_conn.close()
        return elapsed, len(rows), exec_plan

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