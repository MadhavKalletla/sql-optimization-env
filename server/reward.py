# server/reward.py
"""
Reward Composer — computes the 5-dimension weighted reward per PDF spec.

    reward = 0.35 * speedup + 0.25 * equivalence + 0.20 * pattern
           + 0.10 * index   + 0.10 * simplicity   - penalties

Each grader returns a score in [0.0, 1.0].  Weights are applied HERE,
not inside the graders (FIX from original).
"""

from pathlib import Path
from .models import SQLOptReward, SQLOptAction
from .graders.speedup_grader import SpeedupGrader
from .graders.equivalence_grader import EquivalenceGrader
from .graders.antipattern_grader import AntiPatternGrader
from .graders.index_grader import IndexGrader


class RewardComposer:

    WEIGHTS = {
        "speedup":     0.35,
        "equivalence": 0.25,
        "pattern":     0.20,
        "index":       0.10,
        "simplicity":  0.10,
    }

    PENALTIES = {
        "syntax_error":        -0.30,
        "wrong_results":       -0.20,
        "slower_query":        -0.10,
        "timeout_per_second":  -0.05,
        "hack_detected":       -0.40,
    }

    def __init__(self):
        self.speedup_grader = SpeedupGrader()
        self.equiv_grader = EquivalenceGrader()
        self.pattern_grader = AntiPatternGrader()
        self.index_grader = IndexGrader()

    def compute(
        self,
        task,
        action: SQLOptAction,
        orig_time: float,
        opt_time: float,
        opt_rows,
        opt_plan,
        hack,
        query_error,
        db_path: Path = None,
    ) -> SQLOptReward:

        penalty = 0.0

        # ❗ Handle query failure immediately
        if query_error:
            return SQLOptReward(
                total=0.0,
                speedup_score=0.0,
                equivalence_score=0.0,
                pattern_score=0.0,
                index_score=0.0,
                simplicity_score=0.0,
                penalties=self.PENALTIES["syntax_error"],
                speedup_ratio=0.0,
                hack_detected=bool(hack),
                hack_type=hack,
            )

        # ── 1. Speedup Score ─────────────────────────────────────────────
        speedup_raw = self.speedup_grader.grade(orig_time, opt_time)

        # ✅ FIX: prevent invalid division
        if orig_time <= 0:
            speedup_ratio = 0.0
        else:
            speedup_ratio = orig_time / max(opt_time, 0.001)

        if speedup_ratio < 1.0:
            penalty += self.PENALTIES["slower_query"]

        # ── 2. Equivalence Score ─────────────────────────────────────────
        equiv_raw = self.equiv_grader.grade(
            task, action.optimized_query, db_path=db_path
        )

        if equiv_raw < 0.5:
            penalty += self.PENALTIES["wrong_results"]

        # ── 3. Anti-pattern Score ────────────────────────────────────────
        pattern_raw = self.pattern_grader.grade(task, action)

        # ── 4. Index Score ───────────────────────────────────────────────
        index_raw = self.index_grader.grade(task, action, opt_plan)

        # ── 5. Simplicity Score ──────────────────────────────────────────
        simplicity_raw = self._simplicity_score(
            task.slow_query, action.optimized_query
        )

        # ── ⏱ Timeout penalty (>5 s) ─────────────────────────────────────
        if opt_time > 5000:
            penalty += self.PENALTIES["timeout_per_second"] * (
                (opt_time / 1000) - 5
            )

        # ── 🚨 Hack detection ────────────────────────────────────────────
        if hack:
            penalty += self.PENALTIES["hack_detected"]

        # ── Weighted sum ─────────────────────────────────────────────────
        raw_total = (
            self.WEIGHTS["speedup"]     * speedup_raw
            + self.WEIGHTS["equivalence"] * equiv_raw
            + self.WEIGHTS["pattern"]     * pattern_raw
            + self.WEIGHTS["index"]       * index_raw
            + self.WEIGHTS["simplicity"]  * simplicity_raw
            + penalty
        )

        total = round(max(0.0, min(1.0, raw_total)), 4)

        return SQLOptReward(
            total=total,
            speedup_score=round(self.WEIGHTS["speedup"] * speedup_raw, 4),
            equivalence_score=round(self.WEIGHTS["equivalence"] * equiv_raw, 4),
            pattern_score=round(self.WEIGHTS["pattern"] * pattern_raw, 4),
            index_score=round(self.WEIGHTS["index"] * index_raw, 4),
            simplicity_score=round(self.WEIGHTS["simplicity"] * simplicity_raw, 4),
            penalties=round(penalty, 4),
            speedup_ratio=round(speedup_ratio, 2),
            hack_detected=bool(hack),
            hack_type=hack,
        )

    @staticmethod
    def _simplicity_score(original: str, optimized: str) -> float:
        """
        Reward simpler queries (avoid whitespace tricks).
        """

        # ✅ FIX: normalize whitespace (prevents cheating)
        orig_len = len(" ".join(original.split()))
        opt_len = len(" ".join(optimized.split()))

        # ✅ FIX: allow small margin instead of strict ≤
        if opt_len <= orig_len * 1.1:
            return 1.0

        ratio = orig_len / max(opt_len, 1)
        return max(0.0, ratio)