# tasks/hard/railway_tatkal_workload.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="railway_tatkal_workload",
    goal=(
        "An IRCTC operations manager wants a Tatkal booking report: for each train, "
        "show total Tatkal bookings, confirmed seats, waitlist count, and average fare "
        "for a given journey date range (June-July 2025). "
        "The current query has TWO anti-patterns: (1) a correlated subquery that runs "
        "once per booking to count waitlist entries (N+1), and (2) a Cartesian product "
        "caused by joining railway_trains and railway_pnr_bookings without a proper "
        "ON condition inside a subquery. "
        "Fix both patterns: rewrite into a single aggregated JOIN query and add a "
        "composite index on (train_no, journey_date, booked_via)."
    ),
    slow_query="""
        SELECT
            t.train_no,
            t.train_name,
            t.source_station,
            t.dest_station,
            COUNT(b.pnr_number) AS total_tatkal,
            SUM(CASE WHEN b.booking_status = 'CNF' THEN 1 ELSE 0 END) AS confirmed_count,
            (
                SELECT COUNT(*)
                FROM railway_pnr_bookings wl, railway_trains tr
                WHERE wl.booking_status LIKE 'WL%'
                  AND wl.journey_date BETWEEN '2025-06-01' AND '2025-07-31'
            ) AS total_waitlist_all_trains,
            AVG(b.fare_amount) AS avg_tatkal_fare
        FROM railway_trains t, railway_pnr_bookings b
        WHERE b.booked_via = 'TATKAL'
          AND b.journey_date BETWEEN '2025-06-01' AND '2025-07-31'
        GROUP BY t.train_no, t.train_name, t.source_station, t.dest_station
        ORDER BY total_tatkal DESC
    """,
    expected_pattern="N_PLUS_ONE",
    tables=["railway_trains", "railway_pnr_bookings"],
    schema_ddl=load_schema("railway_schema.sql"),
    difficulty="hard",
    curriculum_level=4,
    max_steps=5,
    hint="",
    reference_fix="""
        CREATE INDEX idx_pnr_tatkal_date
            ON railway_pnr_bookings(booked_via, journey_date, train_no, booking_status);

        WITH waitlist_summary AS (
            SELECT train_no, COUNT(*) AS waitlist_count
            FROM railway_pnr_bookings
            WHERE booking_status LIKE 'WL%'
              AND journey_date BETWEEN '2025-06-01' AND '2025-07-31'
            GROUP BY train_no
        )
        SELECT
            t.train_no, t.train_name, t.source_station, t.dest_station,
            COUNT(b.pnr_number) AS total_tatkal,
            SUM(CASE WHEN b.booking_status = 'CNF' THEN 1 ELSE 0 END) AS confirmed_count,
            COALESCE(ws.waitlist_count, 0) AS waitlist_count,
            ROUND(AVG(b.fare_amount), 2) AS avg_tatkal_fare
        FROM railway_trains t
        INNER JOIN railway_pnr_bookings b ON b.train_no = t.train_no
        LEFT JOIN waitlist_summary ws ON ws.train_no = t.train_no
        WHERE b.booked_via = 'TATKAL'
          AND b.journey_date BETWEEN '2025-06-01' AND '2025-07-31'
        GROUP BY t.train_no, t.train_name, t.source_station, t.dest_station, ws.waitlist_count
        ORDER BY total_tatkal DESC
    """,
)
