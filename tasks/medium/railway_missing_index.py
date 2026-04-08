from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="railway_missing_index",
    goal=(
        "A railway operations team needs all bookings for a specific journey date. "
        "The query does a full table scan across all PNR records. "
        "Add an index on journey_date to avoid the full scan."
    ),
    slow_query="""
        SELECT pnr_number, train_no, passenger_name, seat_no, booking_status
        FROM railway_pnr_bookings
        WHERE journey_date = '2025-03-15'
        ORDER BY train_no
    """,
    expected_pattern="MISSING_INDEX",
    tables=["railway_pnr_bookings"],
    schema_ddl=load_schema("railway_schema.sql"),
    difficulty="medium",
    curriculum_level=2,
    hint="The WHERE clause filters on journey_date which has no index. CREATE INDEX idx_rpb_journey_date ON railway_pnr_bookings(journey_date);",
    reference_fix="""
        CREATE INDEX idx_rpb_journey_date ON railway_pnr_bookings(journey_date);
        SELECT pnr_number, train_no, passenger_name, seat_no, booking_status
        FROM railway_pnr_bookings
        WHERE journey_date = '2025-03-15'
        ORDER BY train_no
    """,
)
