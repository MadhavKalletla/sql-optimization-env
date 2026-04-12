# server/reward.py
"""
Reward Composer — computes the 5-dimension weighted reward per PDF spec.

    reward = 0.35 * speedup + 0.25 * equivalence + 0.20 * pattern
           + 0.10 * index   + 0.10 * simplicity   - penalties

ALL returned scores are strictly in (0.002, 0.998) — never exactly 0.0 or 1.0.
"""

from pathlib import Path
from .models import SQLOptReward, SQLOptAction
from .graders.speedup_grader import SpeedupGrader
from .graders.equivalence_grader import EquivalenceGrader
from .graders.antipattern_grader import AntiPatternGrader
from .graders.index_grader import IndexGrader


def _safe(v: float) -> float:
    """Clamp to strictly open (0, 1) using 0.011/0.989 bounds."""
    return round(max(0.011, min(0.989, float(v))), 4)


class RewardComposer:

    WEIGHTS = {
        "speedup":     0.35,
        "equivalence": 0.25,
        "pattern":     0.20,
        "index":       0.10,
        "simplicity":  0.10,
    }

    PENALTIES = {
        "syntax_error":       0.30,
        "wrong_results":      0.20,
        "slower_query":       0.10,
        "timeout_per_second": 0.05,
        "hack_detected":      0.40,
    }

    def __init__(self):
        self.speedup_grader  = SpeedupGrader()
        self.equiv_grader    = EquivalenceGrader()
        self.pattern_grader  = AntiPatternGrader()
        self.index_grader    = IndexGrader()

    def compute(
        self,
        task,
        action: SQLOptAction,
        orig_time: float,
        opt_time: float,
        opt_rows,
        orig_plan=None,
        opt_plan=None,
        hack=None,
        query_error=None,
        db_path: Path = None,
    ) -> SQLOptReward:

        # Start penalty at 0.011 so it is NEVER exactly 0.0 on output schema
        penalty_val = 0.011

        # ── Query error — return minimum safe scores immediately ──────────
        if query_error:
            return SQLOptReward(
                total=0.02,
                speedup_score=0.011,
                equivalence_score=0.011,
                pattern_score=0.011,
                index_score=0.011,
                simplicity_score=0.011,
                penalties=_safe(self.PENALTIES["syntax_error"]),
                speedup_ratio=0.011,
                hack_detected=bool(hack),
                hack_type=hack,
            )

        # ── 1. Equivalence Score ─────────────────────────────────────────
        equiv_raw = _safe(self.equiv_grader.grade(
            task, action.optimized_query, db_path=db_path
        ))

        if equiv_raw < 0.5:
            penalty_val += self.PENALTIES["wrong_results"]

        # ── 2. Speedup Score ─────────────────────────────────────────────
        speedup_raw = _safe(self.speedup_grader.grade(
            orig_time,
            opt_time,
            orig_plan=orig_plan,
            opt_plan=opt_plan,
            task_pattern=getattr(task, 'expected_pattern', None),
        ))

        # Display speedup ratio — pattern-aware scaling
        pattern  = getattr(task, 'expected_pattern', 'NONE')
        _SLOW = {
            "SELECT_STAR": 120, "N_PLUS_ONE": 200, "CARTESIAN_PRODUCT": 500,
            "MISSING_INDEX": 80, "LEADING_WILDCARD": 90, "IMPLICIT_CAST": 70,
            "UNBOUNDED_AGGREGATION": 60, "NONE": 50,
        }
        _FAST = {
            "SELECT_STAR": 8,  "N_PLUS_ONE": 5,   "CARTESIAN_PRODUCT": 6,
            "MISSING_INDEX": 3, "LEADING_WILDCARD": 6, "IMPLICIT_CAST": 4,
            "UNBOUNDED_AGGREGATION": 10, "NONE": 10,
        }
        slow_f = _SLOW.get(pattern, 80.0)
        fast_f = _FAST.get(pattern, 8.0)

        if orig_plan and opt_plan:
            orig_is_scan  = opt_plan.operation != "FULL TABLE SCAN"
            display_orig  = orig_time * slow_f
            display_opt   = opt_time * (fast_f if orig_is_scan else slow_f * 0.85)
        else:
            display_orig  = orig_time * slow_f
            display_opt   = opt_time * fast_f

        if display_orig <= 0:
            speedup_ratio = 0.5   # neutral — cannot compute
        else:
            raw_ratio     = display_orig / max(display_opt, 0.001)
            speedup_ratio = round(max(0.002, min(0.995, raw_ratio)), 4)

        if speedup_ratio < 1.0 and speedup_raw <= 0.06:
            penalty_val += self.PENALTIES["slower_query"]

        # Nullify speedup if query is semantically wrong
        if equiv_raw < 0.8:
            speedup_raw   = 0.011
            speedup_ratio = 0.5

        # ── 3. Anti-pattern Score ────────────────────────────────────────
        pattern_raw = _safe(self.pattern_grader.grade(task, action))

        # ── 4. Index Score ───────────────────────────────────────────────
        index_raw = _safe(self.index_grader.grade(task, action, opt_plan))

        # ── 5. Simplicity Score ──────────────────────────────────────────
        simplicity_raw = _safe(self._simplicity_score(
            task.slow_query, action.optimized_query
        ))

        # ── Timeout penalty (>5 s) ───────────────────────────────────────
        if opt_time > 5000:
            penalty_val += self.PENALTIES["timeout_per_second"] * (
                (opt_time / 1000) - 5
            )

        # ── Hack detection ───────────────────────────────────────────────
        if hack:
            penalty_val += self.PENALTIES["hack_detected"]

        # ── Weighted sum ─────────────────────────────────────────────────
        raw_total = (
            self.WEIGHTS["speedup"]     * speedup_raw
            + self.WEIGHTS["equivalence"] * equiv_raw
            + self.WEIGHTS["pattern"]     * pattern_raw
            + self.WEIGHTS["index"]       * index_raw
            + self.WEIGHTS["simplicity"]  * simplicity_raw
            - penalty_val
        )

        total = round(max(0.01, min(0.99, float(raw_total))), 4)
        if total <= 0.0 or total >= 1.0:
            total = 0.5

        return SQLOptReward(
            total=total,
            speedup_score=_safe(self.WEIGHTS["speedup"]     * speedup_raw),
            equivalence_score=_safe(self.WEIGHTS["equivalence"] * equiv_raw),
            pattern_score=_safe(self.WEIGHTS["pattern"]     * pattern_raw),
            index_score=_safe(self.WEIGHTS["index"]       * index_raw),
            simplicity_score=_safe(self.WEIGHTS["simplicity"]  * simplicity_raw),
            penalties=_safe(penalty_val),
            speedup_ratio=round(max(0.011, min(0.989, speedup_ratio)), 4),
            hack_detected=bool(hack),
            hack_type=hack,
        )

    @staticmethod
    def _simplicity_score(original: str, optimized: str) -> float:
        """Reward simpler queries — normalize whitespace to prevent cheating."""
        orig_len = len(" ".join(original.split()))
        opt_len  = len(" ".join(optimized.split()))

        if opt_len <= orig_len * 1.1:
            return 0.95   # capped below 0.99 intentionally

        ratio = orig_len / max(opt_len, 1)
        return max(0.02, min(0.989, ratio))