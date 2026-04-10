export type AntiPatternType =
  | 'N_PLUS_ONE' | 'CARTESIAN_PRODUCT' | 'MISSING_INDEX'
  | 'SELECT_STAR' | 'LEADING_WILDCARD' | 'IMPLICIT_CAST'
  | 'UNBOUNDED_AGGREGATION' | 'NONE';

export interface ExecutionPlan {
  operation: string;
  rows_examined: number;
  rows_returned: number;
  cost_estimate: number;
  using_index: string | null;
  missing_index_hint: string | null;
  explain_raw: string;
}

export interface SQLOptObservation {
  task_id: string;
  step_number: number;
  goal: string;
  schema_ddl: string;
  current_query: string;
  execution_plan: ExecutionPlan;
  execution_time_ms: number;
  row_count: number;
  db_stats: Record<string, {
    row_count?: number
    indexes?: string[]
    [key: string]: unknown
  }>;
  curriculum_level: number;
  anti_pattern_hint: string | null;
  error_message: string | null;
}

export interface SQLOptAction {
  optimized_query: string;
  identified_pattern: AntiPatternType;
  explanation: string;
  index_statements: string[];
  schema_analysis: string;
}

export interface SQLOptReward {
  total: number;
  speedup_score: number;
  equivalence_score: number;
  pattern_score: number;
  index_score: number;
  simplicity_score: number;
  penalties: number;
  speedup_ratio: number;
  hack_detected: boolean;
  hack_type: string | null;
}

export interface StepResult {
  observation: SQLOptObservation;
  reward: number;
  reward_detail: SQLOptReward;
  done: boolean;
  info: Record<string, unknown>;
}

export interface EnvironmentState {
  episode_id: string;
  current_task_id: string;
  current_step: number;
  max_steps: number;
  curriculum_level: number;
  episode_rewards: number[];
  total_episodes: number;
  is_running: boolean;
  recent_scores: number[];
}

export const ANTI_PATTERN_LABELS: Record<AntiPatternType, string> = {
  N_PLUS_ONE: 'N+1 Query',
  CARTESIAN_PRODUCT: 'Cartesian Product',
  MISSING_INDEX: 'Missing Index',
  SELECT_STAR: 'SELECT * Bloat',
  LEADING_WILDCARD: 'Leading Wildcard',
  IMPLICIT_CAST: 'Implicit Cast',
  UNBOUNDED_AGGREGATION: 'Unbounded Aggregation',
  NONE: 'None Detected',
};

export const ANTI_PATTERN_COLORS: Record<AntiPatternType, string> = {
  N_PLUS_ONE: '#FF5252',
  CARTESIAN_PRODUCT: '#FF1744',
  MISSING_INDEX: '#FF9100',
  SELECT_STAR: '#FFD740',
  LEADING_WILDCARD: '#FF9100',
  IMPLICIT_CAST: '#E040FB',
  UNBOUNDED_AGGREGATION: '#FF6D00',
  NONE: '#00E676',
};

export const LEVEL_LABELS: Record<number, string> = {
  1: 'Intro', 2: 'Easy', 3: 'Medium', 4: 'Hard', 5: 'Expert'
};
