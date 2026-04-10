# server/graders/speedup_grader.py
"""
Plan-cost-based speedup scoring.

Primary signal: execution plan operation type (INDEX SCAN vs FULL TABLE SCAN).
Fallback:       timing ratio, only when plans are absent AND times differ >10%.

Returns a value in [0.0, 1.0].  Weight (0.35) is applied by RewardComposer.

Plan scoring table:
  FULL TABLE SCAN → INDEX SCAN      : 0.85  (genuine index improvement)
  FULL TABLE SCAN → FULL TABLE SCAN : 0.10  (no structural improvement)
  INDEX SCAN     → INDEX SCAN       : 0.50  (already optimised, maintained)

Pattern overrides (checked first):
  SELECT_STAR            : 0.70  (column reduction is the fix, not indexing)
  UNBOUNDED_AGGREGATION
    SCAN → SCAN          : 0.55  (WHERE filter added — partial improvement)

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
        task_pattern=None,
    ) -> float:
        # ── 0. Pattern-aware overrides (before plan-cost check) ───────────────
        # SELECT_STAR: column reduction is the fix, not index change.
        # Both queries correctly do FULL TABLE SCAN for this anti-pattern.
        if task_pattern == 'SELECT_STAR':
            return 0.70

        # UNBOUNDED_AGGREGATION: WHERE filter added = real improvement even if
        # both plans remain FULL TABLE SCAN (no index needed for date filters).
        if task_pattern == 'UNBOUNDED_AGGREGATION':
            if orig_plan and opt_plan:
                if (orig_plan.operation == 'FULL TABLE SCAN'
                        and opt_plan.operation == 'FULL TABLE SCAN'):
                    return 0.55  # partial improvement — filter added but still scanning

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