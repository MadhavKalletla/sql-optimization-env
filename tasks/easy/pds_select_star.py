# tasks/easy/pds_select_star.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="pds_select_star",
    goal=(
        "A state government officer needs card_id and district_code of BPL card holders. "
        "The slow query fetches ALL columns (SELECT *), wasting I/O bandwidth across thousands of rows. "
        "Rewrite it to SELECT only card_id and district_code."
    ),
    slow_query="""
        SELECT * FROM ration_card_beneficiaries
        WHERE card_type = 'BPL'
    """,
    expected_pattern="SELECT_STAR",
    tables=["ration_card_beneficiaries"],
    schema_ddl=load_schema("pds_schema.sql"),
    difficulty="easy",
    curriculum_level=1,
    hint="SELECT * fetches all 6 columns. You only need card_id and district_code — use SELECT card_id, district_code.",
    reference_fix="""
        SELECT card_id, district_code
        FROM ration_card_beneficiaries
        WHERE card_type = 'BPL'
    """,
)
