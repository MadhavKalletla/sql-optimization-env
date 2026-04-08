from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="gst_unbounded_aggregation",
    goal=(
        "A GST analyst wants total taxable value per state. "
        "The query aggregates all rows with no date filter, scanning millions of records. "
        "Add a date range filter before the GROUP BY to limit the scan."
    ),
    slow_query="""
        SELECT state_code, SUM(taxable_value) AS total_value, COUNT(*) AS invoice_count
        FROM gst_invoice_records
        GROUP BY state_code
        ORDER BY total_value DESC
    """,
    expected_pattern="UNBOUNDED_AGGREGATION",
    tables=["gst_invoice_records"],
    schema_ddl=load_schema("gst_schema.sql"),
    difficulty="medium",
    curriculum_level=2,
    hint="GROUP BY with no WHERE filter scans every row. Add: WHERE invoice_date >= '2025-01-01' before the GROUP BY.",
    reference_fix="""
        SELECT state_code, SUM(taxable_value) AS total_value, COUNT(*) AS invoice_count
        FROM gst_invoice_records
        WHERE invoice_date >= '2025-01-01'
        GROUP BY state_code
        ORDER BY total_value DESC
    """,
)
