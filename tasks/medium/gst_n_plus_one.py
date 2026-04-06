# tasks/medium/gst_n_plus_one.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="gst_n_plus_one",
    goal=(
        "An accountant wants each GST invoice with its total item count and taxable value. "
        "The current query uses a correlated subquery that executes once per invoice row. "
        "With 50,000 invoices, this means 50,000 separate database calls. "
        "Rewrite using a single JOIN with GROUP BY."
    ),
    slow_query="""
        SELECT
            i.invoice_id,
            i.gstin_supplier,
            i.invoice_date,
            (SELECT COUNT(*) FROM gst_invoice_items it
             WHERE it.invoice_id = i.invoice_id) AS item_count,
            (SELECT SUM(it2.taxable_value) FROM gst_invoice_items it2
             WHERE it2.invoice_id = i.invoice_id) AS total_taxable
        FROM gst_invoice_records i
        WHERE i.state_code = '27'
        AND i.invoice_date >= '2025-01-01'
    """,
    expected_pattern="N_PLUS_ONE",
    tables=["gst_invoice_records", "gst_invoice_items"],
    schema_ddl=load_schema("gst_schema.sql"),
    difficulty="medium",
    curriculum_level=3,
    hint="Each correlated subquery runs once per outer row — replace both with a single LEFT JOIN + GROUP BY.",
    reference_fix="""
        SELECT
            i.invoice_id, i.gstin_supplier, i.invoice_date,
            COUNT(it.item_id) AS item_count,
            SUM(it.taxable_value) AS total_taxable
        FROM gst_invoice_records i
        LEFT JOIN gst_invoice_items it ON it.invoice_id = i.invoice_id
        WHERE i.state_code = '27'
        AND i.invoice_date >= '2025-01-01'
        GROUP BY i.invoice_id, i.gstin_supplier, i.invoice_date
    """,
)
