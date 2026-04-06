# tasks/base_task.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BaseTask:
    task_id: str
    goal: str
    slow_query: str
    expected_pattern: str            # AntiPatternType value
    tables: List[str]
    schema_ddl: str
    difficulty: str                  # easy / medium / hard
    curriculum_level: int            # 1-5
    max_steps: int = 3
    hint: str = ""
    reference_fix: str = ""          # Example optimal query for testing
    original_time_ms: float = 0.0    # Set at episode start
    original_plan: object = None
