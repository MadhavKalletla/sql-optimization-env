from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="mgnrega_count",
    goal=(
        "A government auditor needs workers per state. "
        "The query fetches all 10 columns unnecessarily. "
        "Rewrite to select only worker_id and state_code to reduce data transfer."
    ),
    slow_query="""
        SELECT * FROM mgnrega_workers
        ORDER BY state_code
    """,
    expected_pattern="SELECT_STAR",
    tables=["mgnrega_workers"],
    schema_ddl=load_schema("mgnrega_schema.sql"),
    difficulty="easy",
    curriculum_level=1,
    hint="SELECT * fetches all 10 columns. You only need worker_id and state_code.",
    reference_fix="""
        SELECT worker_id, state_code
        FROM mgnrega_workers
        ORDER BY state_code
    """,
)
