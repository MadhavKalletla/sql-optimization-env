# server/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ─────────────────────────────────────────────────────────────
# Anti-pattern Enum
# ─────────────────────────────────────────────────────────────
class AntiPatternType(str, Enum):
    N_PLUS_ONE = 'N_PLUS_ONE'
    CARTESIAN_PRODUCT = 'CARTESIAN_PRODUCT'
    MISSING_INDEX = 'MISSING_INDEX'
    SELECT_STAR = 'SELECT_STAR'
    LEADING_WILDCARD = 'LEADING_WILDCARD'
    IMPLICIT_CAST = 'IMPLICIT_CAST'
    UNBOUNDED_AGGREGATION = 'UNBOUNDED_AGGREGATION'
    NONE = 'NONE'


# ─────────────────────────────────────────────────────────────
# Execution Plan
# ─────────────────────────────────────────────────────────────
class ExecutionPlan(BaseModel):
    operation: str
    rows_examined: int = Field(ge=0)
    rows_returned: int = Field(ge=0)
    cost_estimate: float = Field(ge=0.0)
    using_index: Optional[str] = None
    missing_index_hint: Optional[str] = None
    explain_raw: str


# ─────────────────────────────────────────────────────────────
# Observation Model
# ─────────────────────────────────────────────────────────────
class SQLOptObservation(BaseModel):
    task_id: str
    step_number: int = Field(ge=0)
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


# ─────────────────────────────────────────────────────────────
# Action Model
# ─────────────────────────────────────────────────────────────
class SQLOptAction(BaseModel):
    optimized_query: str = Field(min_length=1)
    identified_pattern: AntiPatternType = AntiPatternType.NONE
    explanation: str = ''
    index_statements: List[str] = Field(default_factory=list)
    schema_analysis: str = ''


# ─────────────────────────────────────────────────────────────
# Reward Model
# ─────────────────────────────────────────────────────────────
class SQLOptReward(BaseModel):
    total: float = Field(gt=0.0, lt=1.0)
    speedup_score: float = Field(gt=0.0)
    equivalence_score: float = Field(gt=0.0)
    pattern_score: float = Field(gt=0.0)
    index_score: float = Field(gt=0.0)
    simplicity_score: float = Field(gt=0.0)
    penalties: float = Field(le=0.0)  # penalties should be negative or zero
    speedup_ratio: float = Field(gt=0.0)
    hack_detected: bool
    hack_type: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Step Result
# ─────────────────────────────────────────────────────────────
class StepResult(BaseModel):
    observation: SQLOptObservation
    reward: float = Field(gt=0.0, lt=1.0)
    reward_detail: SQLOptReward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Environment State
# ─────────────────────────────────────────────────────────────
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