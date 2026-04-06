# tasks/easy/railway_simple_filter.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="railway_simple_filter",
    goal=(
        "A ticket checker needs to see all Confirmed bookings for train 12723 on a specific date. "
        "The current query scans the entire pnr_bookings table without using any index. "
        "Add a composite index on (train_no, journey_date) to fix it."
    ),
    slow_query="""
        SELECT pnr_number, passenger_name, seat_no, booking_status
        FROM railway_pnr_bookings
        WHERE train_no = '12723'
        AND journey_date = '2025-06-15'
        AND booking_status = 'CNF'
    """,
    expected_pattern="MISSING_INDEX",
    tables=["railway_pnr_bookings", "railway_trains"],
    schema_ddl=load_schema("railway_schema.sql"),
    difficulty="easy",
    curriculum_level=2,
    hint="The WHERE clause filters on train_no and journey_date — a composite index on both will eliminate the full scan.",
    reference_fix="""
        CREATE INDEX idx_pnr_train_date
        ON railway_pnr_bookings(train_no, journey_date);

        SELECT pnr_number, passenger_name, seat_no, booking_status
        FROM railway_pnr_bookings
        WHERE train_no = '12723'
        AND journey_date = '2025-06-15'
        AND booking_status = 'CNF'
    """,
)
