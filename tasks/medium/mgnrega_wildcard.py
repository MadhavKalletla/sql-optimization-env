# tasks/medium/mgnrega_wildcard.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="mgnrega_wildcard",
    goal=(
        "A district officer wants to search for MGNREGA workers whose names contain "
        "the word 'worker'. The current query uses LIKE '%worker%' which prevents "
        "any index usage and forces a full table scan across all worker records. "
        "Rewrite the query to avoid the leading wildcard, or use an FTS-friendly approach. "
        "If the leading wildcard is unavoidable, add a compensating filter on an indexed column "
        "such as state_code to reduce the scan range."
    ),
    slow_query="""
        SELECT w.worker_id, w.worker_name, w.state_code, w.district_code,
               w.gram_panchayat, w.job_card_no, w.wage_rate
        FROM mgnrega_workers w
        WHERE w.worker_name LIKE '%worker%'
        ORDER BY w.state_code, w.worker_name
    """,
    expected_pattern="LEADING_WILDCARD",
    tables=["mgnrega_workers"],
    schema_ddl=load_schema("mgnrega_schema.sql"),
    difficulty="medium",
    curriculum_level=3,
    max_steps=3,
    hint=(
        "LIKE '%word%' with a leading % cannot use a B-tree index. "
        "Try anchoring the search to a suffix: LIKE 'worker%', or add a "
        "restrictive indexed filter (e.g. state_code) before the LIKE clause."
    ),
    reference_fix="""
        SELECT w.worker_id, w.worker_name, w.state_code, w.district_code,
               w.gram_panchayat, w.job_card_no, w.wage_rate
        FROM mgnrega_workers w
        WHERE w.worker_name LIKE 'Worker_%'
        ORDER BY w.state_code, w.worker_name
    """,
)
