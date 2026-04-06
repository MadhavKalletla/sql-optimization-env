# tasks/hard/mgnrega_schema_e.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="mgnrega_schema_e",
    goal=(
        "A state auditor needs the annual MGNREGA payment compliance report for FY 2024-25: "
        "for each gram panchayat, show total workers, total days worked, total wages due, "
        "total wages actually paid, and the payment gap percentage. "
        "The current query is an unbounded aggregation — it JOINs three tables with no date "
        "filter, aggregates ALL historical rows, and uses two uncorrelated subqueries. "
        "Additionally, the query performs CAST(worker_id AS TEXT) on an already-TEXT column, "
        "triggering an implicit cast that disables index usage. "
        "Fix all patterns: add fiscal year filters, collapse subqueries into one GROUP BY pass, "
        "remove the unnecessary CAST, and add covering indexes."
    ),
    slow_query="""
        SELECT
            w.gram_panchayat,
            COUNT(DISTINCT w.worker_id)                        AS total_workers,
            (
                SELECT SUM(a.days_worked)
                FROM mgnrega_attendance a
                WHERE CAST(a.worker_id AS TEXT) = CAST(w.worker_id AS TEXT)
            )                                                  AS total_days,
            (
                SELECT SUM(p.amount_due)
                FROM mgnrega_payments p
                WHERE CAST(p.worker_id AS TEXT) = CAST(w.worker_id AS TEXT)
            )                                                  AS total_amount_due,
            (
                SELECT SUM(p.amount_paid)
                FROM mgnrega_payments p
                WHERE CAST(p.worker_id AS TEXT) = CAST(w.worker_id AS TEXT)
            )                                                  AS total_amount_paid
        FROM mgnrega_workers w
        GROUP BY w.gram_panchayat
        ORDER BY w.gram_panchayat
    """,
    expected_pattern="UNBOUNDED_AGGREGATION",
    tables=["mgnrega_workers", "mgnrega_attendance", "mgnrega_payments"],
    schema_ddl=load_schema("mgnrega_schema.sql"),
    difficulty="hard",
    curriculum_level=5,
    max_steps=5,
    hint="",
    reference_fix="""
        CREATE INDEX idx_att_worker_date
            ON mgnrega_attendance(worker_id, work_date, days_worked);

        CREATE INDEX idx_pay_worker_month
            ON mgnrega_payments(worker_id, payment_month, amount_due, amount_paid);

        CREATE INDEX idx_worker_gp
            ON mgnrega_workers(gram_panchayat, worker_id);

        WITH attendance_agg AS (
            SELECT worker_id, SUM(days_worked) AS total_days
            FROM mgnrega_attendance
            WHERE work_date BETWEEN '2024-04-01' AND '2025-03-31'
            GROUP BY worker_id
        ),
        payment_agg AS (
            SELECT worker_id, SUM(amount_due) AS total_due, SUM(amount_paid) AS total_paid
            FROM mgnrega_payments
            WHERE payment_month BETWEEN '2024-04' AND '2025-03'
            GROUP BY worker_id
        )
        SELECT
            w.gram_panchayat,
            COUNT(DISTINCT w.worker_id) AS total_workers,
            COALESCE(SUM(aa.total_days), 0) AS total_days_worked,
            COALESCE(SUM(pa.total_due), 0) AS total_amount_due,
            COALESCE(SUM(pa.total_paid), 0) AS total_amount_paid,
            CASE WHEN COALESCE(SUM(pa.total_due), 0) = 0 THEN 0.0
                 ELSE ROUND(100.0 * (COALESCE(SUM(pa.total_due), 0) - COALESCE(SUM(pa.total_paid), 0)) / SUM(pa.total_due), 2)
            END AS payment_gap_pct
        FROM mgnrega_workers w
        LEFT JOIN attendance_agg aa ON aa.worker_id = w.worker_id
        LEFT JOIN payment_agg pa ON pa.worker_id = w.worker_id
        GROUP BY w.gram_panchayat
        ORDER BY payment_gap_pct DESC
    """,
)
