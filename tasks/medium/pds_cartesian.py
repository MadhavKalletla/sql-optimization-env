# tasks/medium/pds_cartesian.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="pds_cartesian",
    goal=(
        "A PDS officer wants to find BPL card holders who have NOT collected rations in Jan 2025. "
        "The current query accidentally creates a Cartesian product because the JOIN condition "
        "between beneficiaries and allotments is missing. "
        "Fix the JOIN by adding the correct ON condition between the two tables."
    ),
    slow_query="""
        SELECT r.card_id, r.household_head, r.state_code
        FROM ration_card_beneficiaries r, pds_allotments a
        WHERE r.card_type = 'BPL'
        AND a.month_year = '2025-01'
        AND a.offtake_qty_kg = 0
    """,
    expected_pattern="CARTESIAN_PRODUCT",
    tables=["ration_card_beneficiaries", "pds_allotments"],
    schema_ddl=load_schema("pds_schema.sql"),
    difficulty="medium",
    curriculum_level=3,
    hint="The comma-separated FROM clause with no ON condition creates a Cartesian product. Use explicit JOIN ... ON r.card_id = a.card_id.",
    reference_fix="""
        SELECT r.card_id, r.household_head, r.state_code
        FROM ration_card_beneficiaries r
        JOIN pds_allotments a ON a.card_id = r.card_id
        WHERE r.card_type = 'BPL'
        AND a.month_year = '2025-01'
        AND a.offtake_qty_kg = 0
    """,
)
