from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="mgnrega_implicit_cast",
    goal=(
        "An MGNREGA payment officer queries workers with wage rate above minimum. "
        "The WHERE clause compares wage_rate (DECIMAL column) to a string '250', "
        "causing implicit type cast and disabling index usage. Remove the quotes."
    ),
    slow_query="""
        SELECT worker_id, worker_name, wage_rate, state_code
        FROM mgnrega_workers
        WHERE wage_rate > '250'
        ORDER BY wage_rate DESC
    """,
    expected_pattern="IMPLICIT_CAST",
    tables=["mgnrega_workers"],
    schema_ddl=load_schema("mgnrega_schema.sql"),
    difficulty="hard",
    curriculum_level=3,
    hint="wage_rate is a DECIMAL column. Comparing it to the string '250' (with quotes) forces a type cast. Remove the quotes: WHERE wage_rate > 250",
    reference_fix="""
        SELECT worker_id, worker_name, wage_rate, state_code
        FROM mgnrega_workers
        WHERE wage_rate > 250
        ORDER BY wage_rate DESC
    """,
)
