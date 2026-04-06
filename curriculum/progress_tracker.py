# curriculum/progress_tracker.py
"""
ProgressTracker — per-agent episode history.
Stored as /tmp/progress_<agent_id>.json.
"""

import json
from pathlib import Path
from typing import Optional


class ProgressTracker:
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self._path = Path(f"/tmp/progress_{agent_id}.json")
        self._history: list[dict] = []
        self._load()

    def record(self, task_id: str, reward: float, level: int,
               speedup: float = 0.0, hack: Optional[str] = None) -> None:
        entry = {
            "task_id": task_id,
            "reward": round(reward, 4),
            "level": level,
            "speedup": round(speedup, 2),
            "hack": hack,
            "episode": len(self._history) + 1,
        }
        self._history.append(entry)
        self._save()

    def mean_reward(self, last_n: int = 0) -> float:
        data = self._history[-last_n:] if last_n else self._history
        if not data:
            return 0.0
        return round(sum(e["reward"] for e in data) / len(data), 4)

    def best_reward(self, task_id: Optional[str] = None) -> float:
        data = [e for e in self._history if not task_id or e["task_id"] == task_id]
        return max((e["reward"] for e in data), default=0.0)

    def total_episodes(self) -> int:
        return len(self._history)

    def task_summary(self) -> dict:
        tasks: dict[str, list[float]] = {}
        for e in self._history:
            tasks.setdefault(e["task_id"], []).append(e["reward"])
        return {
            tid: {
                "count": len(rewards),
                "mean": round(sum(rewards) / len(rewards), 4),
                "best": max(rewards),
            }
            for tid, rewards in tasks.items()
        }

    def reset(self) -> None:
        self._history = []
        if self._path.exists():
            self._path.unlink()

    def _load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._history = []

    def _save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._history, f)
        except OSError:
            pass
