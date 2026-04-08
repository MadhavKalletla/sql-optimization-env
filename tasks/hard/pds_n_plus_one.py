from tasks.base_task import BaseTask
from tasks._schema_loader import load_schema

TASK = BaseTask(
    task_id="pds_n_plus_one",
    goal=(
        "A PDS auditor needs BPL beneficiaries with their latest allotment month. "
        "The correlated subquery runs once per beneficiary row — N+1 performance. "
        "Rewrite using a JOIN with GROUP BY."
    ),
    slow_query="""
        SELECT r.card_id, r.household_head, r.district_code,
               (SELECT MAX(a.month_year) FROM pds_allotments a
                WHERE a.card_id = r.card_id) AS last_allotment
        FROM ration_card_beneficiaries r
        WHERE r.card_type = 'BPL'
    """,
    expected_pattern="N_PLUS_ONE",
    tables=["ration_card_beneficiaries", "pds_allotments"],
    schema_ddl=load_schema("pds_schema.sql"),
    difficulty="hard",
    curriculum_level=3,
    hint="The correlated subquery runs once per beneficiary. Replace with LEFT JOIN pds_allotments + GROUP BY.",
    reference_fix="""
        SELECT r.card_id, r.household_head, r.district_code,
               MAX(a.month_year) AS last_allotment
        FROM ration_card_beneficiaries r
        LEFT JOIN pds_allotments a ON r.card_id = a.card_id
        WHERE r.card_type = 'BPL'
        GROUP BY r.card_id, r.household_head, r.district_code
    """,
)
