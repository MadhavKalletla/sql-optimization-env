# server/graders/speedup_grader.py
"""
Plan-cost-based speedup scoring.

Primary signal: execution plan operation type (INDEX SCAN vs FULL TABLE SCAN).
Fallback:       timing ratio, only when plans are absent AND times differ >10%.

Returns a value in [0.0, 1.0].  Weight (0.35) is applied by RewardComposer.

Plan scoring table:
  FULL TABLE SCAN → INDEX SCAN   : 0.85  (genuine index improvement)
  FULL TABLE SCAN → FULL TABLE SCAN : 0.10  (no structural improvement)
  INDEX SCAN     → INDEX SCAN    : 0.50  (already optimised, maintained)

Timing fallback (plans unavailable, |diff| > 10%):
  ratio >= 50  → 1.0
  ratio >= 20  → 0.85
  ratio >= 10  → 0.70
  ratio >= 5   → 0.50
  ratio >= 2   → 0.30
  ratio >= 1.1 → 0.15
  else         → 0.05

Cannot-measure sentinel (plans unavailable AND both times < 2 ms): 0.25
"""


class SpeedupGrader:

    def grade(
        self,
        orig_time_ms: float,
        opt_time_ms: float,
        orig_plan=None,
        opt_plan=None,
    ) -> float:
        # ── 1. Plan-cost-based scoring (primary signal) ──────────────────────
        if orig_plan is not None and opt_plan is not None:
            orig_op = getattr(orig_plan, "operation", None)
            opt_op = getattr(opt_plan, "operation", None)

            if orig_op == "FULL TABLE SCAN" and opt_op == "INDEX SCAN":
                return 0.85  # genuine index improvement

            if orig_op == "FULL TABLE SCAN" and opt_op == "FULL TABLE SCAN":
                return 0.10  # no structural improvement

            if orig_op == "INDEX SCAN" and opt_op == "INDEX SCAN":
                return 0.50  # already optimised, maintained

        # ── 2. Timing-based fallback ──────────────────────────────────────────
        # Cannot-measure sentinel: SQLite on small DBs runs every query in <1 ms,
        # so we cannot distinguish fast vs slow queries by time alone.
        if orig_time_ms < 2.0 and opt_time_ms < 2.0:
            return 0.25  # "we cannot measure" — not a neutral-good signal

        # Only use timing when there is a meaningful difference (> 10 %).
        ratio = orig_time_ms / max(opt_time_ms, 0.001)

        if ratio >= 50:   return 1.0
        if ratio >= 20:   return 0.85
        if ratio >= 10:   return 0.70
        if ratio >= 5:    return 0.50
        if ratio >= 2:    return 0.30
        if ratio >= 1.1:  return 0.15
        return 0.05  # never return 0.0 for timing alone