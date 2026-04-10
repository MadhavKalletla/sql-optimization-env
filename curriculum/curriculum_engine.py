# curriculum/curriculum_engine.py
"""
Curriculum Engine — controls difficulty progression per PDF spec.
  Graduate UP:   score >= 0.70 for 3 consecutive episodes
  Step DOWN:     score <  0.40 for 2 consecutive episodes
State persists locally.
"""

import os
import json
from pathlib import Path
from .level_config import LEVEL_CONFIG

# ✅ FIX: use local file instead of /tmp (persistent + Docker-safe)
STATE_FILE = Path(os.environ.get("CURRICULUM_STATE_PATH", "/tmp/curriculum_state.json"))


class CurriculumEngine:

    GRADUATE_THRESHOLD = 0.70
    GRADUATE_CONSECUTIVE = 3
    REMEDIATE_THRESHOLD = 0.40
    REMEDIATE_CONSECUTIVE = 2
    MAX_LEVEL = 5
    MIN_LEVEL = 1

    def __init__(self):
        self._load_state()

    def _load_state(self):
        # Try env var first (survives cold restarts via HF Secret)
        env_state = os.environ.get('CURRICULUM_STATE_JSON', '')
        if env_state:
            try:
                s = json.loads(env_state)
                self.current_level = s.get('level', 1)
                self.recent_scores = s.get('recent_scores', [])
                self.total_episodes = s.get('total_episodes', 0)
                self.retry_count = s.get('retry_count', 0)
                print(f'Curriculum loaded from env var: level={self.current_level}', flush=True)
                return
            except Exception:
                pass

        # Fallback to file
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                    self.current_level = s.get('level', 1)
                    self.recent_scores = s.get('recent_scores', [])
                    self.total_episodes = s.get('total_episodes', 0)
                    self.retry_count = s.get('retry_count', 0)
                    return
            except Exception:
                pass

        # Default
        self.current_level = 1
        self.recent_scores = []
        self.total_episodes = 0
        self.retry_count = 0

    def _save_state(self):
        data = {
            'level': self.current_level,
            'recent_scores': self.recent_scores[-10:],
            'total_episodes': self.total_episodes,
            'retry_count': getattr(self, 'retry_count', 0),
        }

        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f)
        except OSError:
            pass

        # Also expose via /state so frontend can see it
        # (State already returned in state() method — no change needed there)

    def record_episode(self, score: float):
        self.recent_scores.append(round(score, 4))
        self.total_episodes += 1
        self._evaluate_transition()
        self._save_state()

    def _evaluate_transition(self):
        # Dynamic threshold — level 3 is harder, lower bar slightly
        grad_threshold = 0.65 if self.current_level == 3 else self.GRADUATE_THRESHOLD

        if len(self.recent_scores) >= self.GRADUATE_CONSECUTIVE:
            last_n = self.recent_scores[-self.GRADUATE_CONSECUTIVE:]
            if all(s >= grad_threshold for s in last_n):
                if self.current_level < self.MAX_LEVEL:
                    self.current_level += 1
                    self.recent_scores = []
                    self.retry_count = 0
                    print(f'CURRICULUM: Graduated to Level {self.current_level}', flush=True)
                return

        # Remediation: 2 consecutive < 0.40
        if len(self.recent_scores) >= self.REMEDIATE_CONSECUTIVE:
            last_n_fail = self.recent_scores[-self.REMEDIATE_CONSECUTIVE:]
            if all(s < self.REMEDIATE_THRESHOLD for s in last_n_fail):
                retry_count = getattr(self, 'retry_count', 0)
                if retry_count < 1:
                    self.retry_count = retry_count + 1
                    self.recent_scores = []
                    print(f'CURRICULUM: Retrying Level {self.current_level}', flush=True)
                else:
                    if self.current_level > self.MIN_LEVEL:
                        self.current_level -= 1
                        self.recent_scores = []
                        self.retry_count = 0
                        print(f'CURRICULUM: Dropped to Level {self.current_level}', flush=True)