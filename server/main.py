# server/main.py
"""
FastAPI application — OpenEnv-compliant endpoints.
GET /health, GET /reset, POST /reset, POST /step, GET /state
"""

import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .environment import SQLOptEnvironment
from .models import SQLOptAction, SQLOptObservation, EnvironmentState, StepResult, ResetResponse

env: SQLOptEnvironment = None

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DB = ROOT / "data" / "fixtures" / "benchmark_seed42.db"
SCHEMA_DIR = ROOT / "data" / "schemas"


# ─────────────────────────────────────────────────────────────
# DOMAIN SPECS
# ─────────────────────────────────────────────────────────────
DOMAIN_SPECS: list[dict[str, Any]] = [
    {
        "id": "gst",
        "name": "GST",
        "description": "Goods & Services Tax — B2B invoices, HSN line items, intra/inter-state tax splits.",
        "schema_file": "gst_schema.sql",
        "tables": ["gst_invoice_records", "gst_invoice_items"],
        "real_world_scale": "At 100k invoice scale: ~100k header rows and ~300k line items.",
        "sample_queries": [
            "SELECT state_code, COUNT(*) AS invoices FROM gst_invoice_records GROUP BY state_code ORDER BY invoices DESC LIMIT 10;",
            "SELECT gstin_supplier, COUNT(*) FROM gst_invoice_records WHERE invoice_date >= '2025-01-01' GROUP BY gstin_supplier ORDER BY COUNT(*) DESC LIMIT 5;",
        ],
    },
    {
        "id": "pds",
        "name": "PDS",
        "description": "Public Distribution System — ration cards, monthly allotments, fair-price shops.",
        "schema_file": "pds_schema.sql",
        "tables": ["ration_card_beneficiaries", "pds_allotments"],
        "real_world_scale": "At 100k seed: ~20k cardholders and ~80k+ allotment rows.",
        "sample_queries": [
            "SELECT state_code, COUNT(*) FROM ration_card_beneficiaries GROUP BY state_code;",
            "SELECT commodity, SUM(offtake_qty_kg) FROM pds_allotments GROUP BY commodity;",
        ],
    },
    {
        "id": "railway",
        "name": "Railway (IRCTC-style)",
        "description": "Train master and PNR bookings — Tatkal / availability style workloads.",
        "schema_file": "railway_schema.sql",
        "tables": ["railway_trains", "railway_pnr_bookings"],
        "real_world_scale": "Fixed train catalog plus booking volume; journey dates skew to festival months.",
        "sample_queries": [
            "SELECT train_no, journey_date, COUNT(*) FROM railway_pnr_bookings GROUP BY train_no, journey_date ORDER BY COUNT(*) DESC LIMIT 15;",
        ],
    },
    {
        "id": "mgnrega",
        "name": "MGNREGA",
        "description": "Rural employment guarantee — workers, muster attendance, wage payments.",
        "schema_file": "mgnrega_schema.sql",
        "tables": ["mgnrega_workers", "mgnrega_attendance", "mgnrega_payments"],
        "real_world_scale": "Worker count ~ n/3 of GST invoices; attendance and payment rows scale with workers.",
        "sample_queries": [
            "SELECT state_code, COUNT(*) FROM mgnrega_workers GROUP BY state_code;",
        ],
    },
]


# ─────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────
def _fixture_db_path() -> Path:
    if env is not None and getattr(env, "_db_path", None):
        return env._db_path
    return FIXTURE_DB


def _table_row_counts() -> dict[str, int]:
    db = _fixture_db_path()
    if not db.is_file():
        return {}
    out: dict[str, int] = {}
    conn = sqlite3.connect(str(db))
    try:
        names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        for name in names:
            try:
                out[name] = int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
            except sqlite3.Error:
                out[name] = -1
    finally:
        conn.close()
    return out


# ─────────────────────────────────────────────────────────────
# APP LIFECYCLE
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global env
    env = SQLOptEnvironment()
    print("✅ Environment initialized", flush=True)
    yield


app = FastAPI(
    title="SQL Optimization RL Environment",
    description="OpenEnv-compliant SQL optimization environment with Indian data domains",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount Next.js static assets
_next_dir = ROOT / "static" / "_next"
if _next_dir.exists():
    app.mount("/_next", StaticFiles(directory=str(_next_dir)), name="nextjs-assets")


# ─────────────────────────────────────────────────────────────
# UI ROUTES
# ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    f = ROOT / "static" / "index.html"
    return HTMLResponse(content=f.read_text(encoding="utf-8") if f.exists() else "<h1>Not found</h1>")


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dashboard/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page():
    f = ROOT / "static" / "dashboard" / "index.html"
    return HTMLResponse(content=f.read_text(encoding="utf-8") if f.exists() else "<h1>Not found</h1>")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    f = ROOT / "static" / "favicon.ico"
    return FileResponse(str(f)) if f.exists() else HTMLResponse("", status_code=404)


# ─────────────────────────────────────────────────────────────
# HEALTH + PING (keep-alive)
# ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    row_counts = _table_row_counts()
    return {
        "status": "ok",
        "environment": "sql-optimization-env",
        "version": "1.0.0",
        "database_path": str(_fixture_db_path()),
        "table_row_counts": row_counts,
        "total_rows": sum(v for v in row_counts.values() if v >= 0),
    }


@app.get("/ping")
async def ping():
    """Keep-alive endpoint — called every 30s by frontend to prevent HF cold start."""
    return {"status": "alive", "ts": time.time()}


# ─────────────────────────────────────────────────────────────
# DOMAINS
# ─────────────────────────────────────────────────────────────
@app.get("/domains")
async def domains():
    row_counts = _table_row_counts()
    payload: list[dict[str, Any]] = []
    for spec in DOMAIN_SPECS:
        schema_path = SCHEMA_DIR / spec["schema_file"]
        ddl = (
            schema_path.read_text(encoding="utf-8")
            if schema_path.is_file()
            else f"-- Schema file not found: {schema_path.name}\n"
        )
        tables_out = [{"table": t, "row_count": row_counts.get(t, 0)} for t in spec["tables"]]
        payload.append({
            "domain": spec["name"],
            "id": spec["id"],
            "description": spec["description"],
            "real_world_scale": spec["real_world_scale"],
            "tables": tables_out,
            "sample_queries": spec["sample_queries"],
            "schema_ddl": ddl,
        })
    return {"domains": payload}


# ─────────────────────────────────────────────────────────────
# OPENENV CORE ENDPOINTS
# ─────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: Optional[str] = None


# ── GET /reset — browser friendly, no body ───────────────────
@app.get("/reset", response_model=ResetResponse)
async def reset_get(task_id: Optional[str] = Query(default=None)):
    """Reset the environment. Pass task_id as query param: /reset?task_id=gst_missing_index"""
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    try:
        obs = env.reset(task_id=task_id)
        return {"observation": obs.dict(), "info": {}}
    except Exception as e:
        print(f"[RESET ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /reset — validator + inference.py friendly ──────────
@app.post("/reset", response_model=ResetResponse)
async def reset_post(
    task_id_query: Optional[str] = Query(default=None, alias="task_id"),
    body: Optional[ResetRequest] = Body(default=None),
):
    """Reset the environment. task_id can be in query param OR JSON body."""
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    resolved = (body.task_id if body else None) or task_id_query
    try:
        obs = env.reset(task_id=resolved)
        return {"observation": obs.dict(), "info": {}}
    except Exception as e:
        print(f"[RESET ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /step ────────────────────────────────────────────────
@app.post("/step", response_model=StepResult)
async def step(action: SQLOptAction):
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    try:
        return env.step(action)
    except Exception as e:
        print(f"[STEP ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /state ────────────────────────────────────────────────
@app.get("/state", response_model=EnvironmentState)
async def state():
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    try:
        return env.state()
    except Exception as e:
        print(f"[STATE ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /tasks ────────────────────────────────────────────────
@app.get("/tasks")
async def list_tasks():
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")
    try:
        tasks = env.task_registry.all_tasks()
        return [
            {
                "task_id": t.task_id,
                "difficulty": t.difficulty,
                "curriculum_level": t.curriculum_level,
                "expected_pattern": t.expected_pattern,
                "tables": t.tables,
            }
            for t in tasks
        ]
    except Exception as e:
        print(f"[TASK ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# UTILITY ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/validate")
async def validate_sql(body: dict = Body(...)):
    """Validate SQL syntax without executing."""
    query = body.get("query", "").strip()
    if not query:
        return {"valid": False, "error": "Empty query"}
    if env is None:
        return {"valid": False, "error": "Environment not initialized"}
    try:
        conn = sqlite3.connect(str(env._db_path))
        conn.execute(f"EXPLAIN {query}")
        conn.close()
        return {"valid": True, "error": None}
    except sqlite3.Error as e:
        return {"valid": False, "error": str(e)}


@app.get("/curriculum/export")
async def export_curriculum():
    import json
    if env is None:
        return {"state": "{}"}
    c = env.curriculum
    return {
        "state": json.dumps({
            "level": c.current_level,
            "recent_scores": c.recent_scores,
            "total_episodes": c.total_episodes,
        })
    }


@app.post("/grade")
async def grade_task(body: dict = Body(...)):
    """
    Grade a task submission directly.
    Returns score strictly between 0.002 and 0.998 (never exactly 0 or 1).

    Body: { "task_id": "gst_missing_index", "action": { ...SQLOptAction fields... } }
    """
    if env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized")

    task_id = body.get("task_id")
    action_data = body.get("action")

    if not task_id or not action_data:
        raise HTTPException(status_code=400, detail="Missing task_id or action")

    try:
        task = env.task_registry.get_task_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

        action = SQLOptAction(**action_data)

        orig_time, orig_rows, orig_plan = env._run_query(task.slow_query)
        task.original_time_ms = orig_time
        task.original_plan = orig_plan

        query_error = None
        try:
            opt_time, opt_rows, opt_plan = env._run_query(
                action.optimized_query, action.index_statements
            )
        except Exception as e:
            opt_time = orig_time * 3.0
            opt_rows = 0
            opt_plan = None
            query_error = str(e)

        reward_detail = env.reward_composer.compute(
            task=task,
            action=action,
            orig_time=orig_time,
            opt_time=opt_time,
            opt_rows=opt_rows,
            orig_plan=orig_plan,
            opt_plan=opt_plan,
            hack=env.hack_detector.detect(action, task),
            query_error=query_error,
            db_path=env._db_path,
        )

        # Strictly between 0 and 1
        score = round(max(0.002, min(0.998, float(reward_detail.total))), 4)

        return {
            "score": score,
            "task_id": task_id,
            "details": {
                "speedup_score": reward_detail.speedup_score,
                "equivalence_score": reward_detail.equivalence_score,
                "pattern_score": reward_detail.pattern_score,
                "index_score": reward_detail.index_score,
                "simplicity_score": reward_detail.simplicity_score,
                "penalties": reward_detail.penalties,
                "speedup_ratio": reward_detail.speedup_ratio,
                "hack_detected": reward_detail.hack_detected,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[GRADE ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))