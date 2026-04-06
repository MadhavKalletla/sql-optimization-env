# tasks/easy/gst_missing_index.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="gst_missing_index",
    goal=(
        "A supplier needs all their invoices for the last quarter. "
        "The current query does a full table scan across 100,000 rows. "
        "Optimize it so it uses an index on gstin_supplier and runs in <50ms."
    ),
    slow_query="""
        SELECT invoice_id, invoice_date, taxable_value, igst_amount, state_code
        FROM gst_invoice_records
        WHERE gstin_supplier = '27AABCU9603R1ZX'
        AND invoice_date >= '2025-01-01'
        ORDER BY invoice_date DESC
    """,
    expected_pattern="MISSING_INDEX",
    tables=["gst_invoice_records"],
    schema_ddl=load_schema("gst_schema.sql"),
    difficulty="easy",
    curriculum_level=2,
    hint="The WHERE clause filters on gstin_supplier — check if that column is indexed.",
    reference_fix="""
        CREATE INDEX idx_gst_supplier_date
        ON gst_invoice_records(gstin_supplier, invoice_date DESC);

        SELECT invoice_id, invoice_date, taxable_value, igst_amount, state_code
        FROM gst_invoice_records
        WHERE gstin_supplier = '27AABCU9603R1ZX'
        AND invoice_date >= '2025-01-01'
        ORDER BY invoice_date DESC
    """,
)
