# server/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class AntiPatternType(str, Enum):
    N_PLUS_ONE = 'N_PLUS_ONE'
    CARTESIAN_PRODUCT = 'CARTESIAN_PRODUCT'
    MISSING_INDEX = 'MISSING_INDEX'
    SELECT_STAR = 'SELECT_STAR'
    LEADING_WILDCARD = 'LEADING_WILDCARD'
    IMPLICIT_CAST = 'IMPLICIT_CAST'
    UNBOUNDED_AGGREGATION = 'UNBOUNDED_AGGREGATION'
    NONE = 'NONE'


class ExecutionPlan(BaseModel):
    operation: str
    rows_examined: int = Field(ge=0)
    rows_returned: int = Field(ge=0)
    cost_estimate: float = Field(ge=0.0)
    using_index: Optional[str] = None
    missing_index_hint: Optional[str] = None
    explain_raw: str = ""


class SQLOptObservation(BaseModel):
    task_id: str
    step_count: int = Field(ge=0)
    goal: str
    schema_ddl: str
    current_query: str
    execution_plan: ExecutionPlan
    execution_time_ms: float = Field(ge=0.0)
    row_count: int = Field(ge=0)
    db_stats: Dict[str, Any]
    curriculum_level: int = Field(ge=1, le=5)
    anti_pattern_hint: Optional[str] = None
    error_message: Optional[str] = None


class SQLOptAction(BaseModel):
    optimized_query: str = Field(min_length=1)
    identified_pattern: AntiPatternType = AntiPatternType.NONE
    explanation: str = ''
    index_statements: List[str] = Field(default_factory=list)
    schema_analysis: str = ''


class SQLOptReward(BaseModel):
    total: float = 0.5
    speedup_score: float = 0.0
    equivalence_score: float = 0.0
    pattern_score: float = 0.0
    index_score: float = 0.0
    simplicity_score: float = 0.0
    penalties: float = 0.0
    speedup_ratio: float = 0.0
    hack_detected: bool = False
    hack_type: Optional[str] = None

class StepResult(BaseModel):
    observation: SQLOptObservation
    reward: float = 0.5
    reward_detail: SQLOptReward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetResponse(BaseModel):
    observation: SQLOptObservation
    info: Dict[str, Any] = Field(default_factory=dict)


class EnvironmentState(BaseModel):
    episode_id: str
    current_task_id: str
    current_step: int = Field(ge=0)
    max_steps: int = Field(gt=0)
    curriculum_level: int = Field(ge=1, le=5)
    episode_rewards: List[float] = Field(default_factory=list)
    total_episodes: int = Field(ge=0)
    is_running: bool
    recent_scores: List[float] = Field(default_factory=list)