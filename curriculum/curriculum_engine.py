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
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)

                self.current_level = s.get("level", 1)
                self.recent_scores = s.get("recent_scores", [])
                self.total_episodes = s.get("total_episodes", 0)

            except (json.JSONDecodeError, OSError):
                self.current_level = 1
                self.recent_scores = []
                self.total_episodes = 0
        else:
            self.current_level = 1
            self.recent_scores = []
            self.total_episodes = 0

    def _save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(
                    {
                        "level": self.current_level,
                        "recent_scores": self.recent_scores[-10:],
                        "total_episodes": self.total_episodes,
                    },
                    f,
                )
        except OSError:
            pass

    def record_episode(self, score: float):
        self.recent_scores.append(round(score, 4))
        self.total_episodes += 1
        self._evaluate_transition()
        self._save_state()

    def _evaluate_transition(self):
        # ── Graduation check ─────────────────────────────────────────────
        if len(self.recent_scores) >= self.GRADUATE_CONSECUTIVE:
            last_n = self.recent_scores[-self.GRADUATE_CONSECUTIVE:]
            if all(s >= self.GRADUATE_THRESHOLD for s in last_n):
                if self.current_level < self.MAX_LEVEL:
                    self.current_level += 1
                    self.recent_scores = []
                    print(f"CURRICULUM: Graduated to Level {self.current_level}")
                return

        # ── Remediation check ────────────────────────────────────────────
        if len(self.recent_scores) >= self.REMEDIATE_CONSECUTIVE:
            last_n_fail = self.recent_scores[-self.REMEDIATE_CONSECUTIVE:]
            if all(s < self.REMEDIATE_THRESHOLD for s in last_n_fail):
                if self.current_level > self.MIN_LEVEL:
                    self.current_level -= 1
                    self.recent_scores = []
                    print(f"CURRICULUM: Stepped down to Level {self.current_level}")