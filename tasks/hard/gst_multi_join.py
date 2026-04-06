# tasks/hard/gst_multi_join.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="gst_multi_join",
    goal=(
        "A tax auditor needs a reconciliation report: for each supplier in Maharashtra, "
        "show total invoices, total taxable value, total GST paid, and count of line items. "
        "The query uses a correlated subquery with a nested IN clause across 2M rows — "
        "a classic N+1 combined with a missing index. "
        "Optimize for <2 second execution. Multiple anti-patterns are present."
    ),
    slow_query="""
        SELECT
            r.gstin_supplier,
            COUNT(DISTINCT r.invoice_id) AS invoice_count,
            SUM(r.taxable_value) AS total_taxable,
            SUM(r.cgst_amount + r.sgst_amount + r.igst_amount) AS total_gst,
            (SELECT COUNT(*) FROM gst_invoice_items
             WHERE invoice_id IN (
                 SELECT invoice_id FROM gst_invoice_records
                 WHERE gstin_supplier = r.gstin_supplier
             )) AS item_count
        FROM gst_invoice_records r
        WHERE r.state_code = '27'
        GROUP BY r.gstin_supplier
    """,
    expected_pattern="N_PLUS_ONE",
    tables=["gst_invoice_records", "gst_invoice_items"],
    schema_ddl=load_schema("gst_schema.sql"),
    difficulty="hard",
    curriculum_level=4,
    max_steps=5,
    hint="",
    reference_fix="""
        CREATE INDEX idx_gst_state_supplier
        ON gst_invoice_records(state_code, gstin_supplier);

        CREATE INDEX idx_items_invoice
        ON gst_invoice_items(invoice_id);

        SELECT
            r.gstin_supplier,
            COUNT(DISTINCT r.invoice_id) AS invoice_count,
            SUM(r.taxable_value) AS total_taxable,
            SUM(r.cgst_amount + r.sgst_amount + r.igst_amount) AS total_gst,
            COUNT(it.item_id) AS item_count
        FROM gst_invoice_records r
        LEFT JOIN gst_invoice_items it ON it.invoice_id = r.invoice_id
        WHERE r.state_code = '27'
        GROUP BY r.gstin_supplier
    """,
)
