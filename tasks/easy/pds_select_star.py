# tasks/easy/pds_select_star.py
from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="pds_select_star",
    goal=(
        "A state government officer wants a count of BPL card holders by district. "
        "The query fetches all columns from 80,000 rows but only needs card_id and district_code. "
        "Rewrite it to select only required columns and add appropriate filter."
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
    hint="SELECT * fetches all 12 columns. You only need card_id and district_code.",
    reference_fix="""
        SELECT card_id, district_code
        FROM ration_card_beneficiaries
        WHERE card_type = 'BPL'
    """,
)
