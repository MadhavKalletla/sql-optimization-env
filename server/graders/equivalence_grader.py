# server/graders/equivalence_grader.py
"""
Equivalence grader — checks that the optimized query produces semantically
equivalent results to the reference (or slow) query.

Scoring:
  - Exact match (same rows, same values):        1.0
  - Jaccard similarity (set overlap):            0.0–1.0
  - Row-count ratio (soft penalty for mismatch): applied as weight

FIX: The old strict `return 0.0 if row counts differ` was too harsh.
     An optimized query that returns a subset or superset of columns but
     preserves row identity should still score well.
     Now we use a soft row-count ratio multiplier instead.
"""

import sqlite3
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB = _ROOT / "data" / "fixtures" / "benchmark_seed42.db"


class EquivalenceGrader:

    def grade(self, task, optimized_query: str, db_path: Path = None) -> float:
        db = db_path or _DEFAULT_DB
        conn = sqlite3.connect(str(db))

        try:
            # For SELECT_STAR tasks the reference_fix is the semantic baseline.
            # Any other task — the slow_query itself is the baseline.
            baseline_query = task.slow_query
            if getattr(task, "expected_pattern", None) == "SELECT_STAR":
                ref_fix = (getattr(task, "reference_fix", "") or "").strip()
                if ref_fix:
                    baseline_query = ref_fix

            try:
                baseline_rows = list(map(tuple, conn.execute(baseline_query).fetchall()))
            except Exception:
                # If baseline itself fails, we can't compare — give neutral score
                return 0.5

            try:
                opt_rows = list(map(tuple, conn.execute(optimized_query).fetchall()))
            except Exception:
                return 0.001   # Syntax / runtime error in optimized query

            n_base = len(baseline_rows)
            n_opt  = len(opt_rows)

            # Empty result edge cases
            if n_base == 0 and n_opt == 0:
                return 0.999
            if n_base == 0:
                return 0.3   # baseline empty but opt returns rows → suspicious
            if n_opt == 0:
                return 0.001   # opt returns nothing → wrong

            # ── Row count ratio (soft, not hard) ────────────────────────────
            # If counts are the same → ratio = 1.0
            # If very different → ratio approaches 0
            count_ratio = min(n_base, n_opt) / max(n_base, n_opt)

            # ── Jaccard similarity on row values ────────────────────────────
            # Compare only the first column of each row to be projection-agnostic.
            # This handles SELECT * vs SELECT card_id, district_code correctly —
            # as long as the key column values match, it's semantically equivalent.
            base_keys = set(r[0] for r in baseline_rows) if baseline_rows and baseline_rows[0] else set()
            opt_keys  = set(r[0] for r in opt_rows)      if opt_rows and opt_rows[0] else set()

            if not base_keys and not opt_keys:
                jaccard = 1.0
            elif not base_keys or not opt_keys:
                jaccard = 0.0
            else:
                intersection = len(base_keys & opt_keys)
                union        = len(base_keys | opt_keys)
                jaccard = intersection / union if union > 0 else 1.0

            # ── Full row set comparison (bonus for exact match) ──────────────
            base_set = set(baseline_rows)
            opt_set  = set(opt_rows)
            exact_overlap = len(base_set & opt_set) / max(len(base_set | opt_set), 1)

            # ── Weighted combination ─────────────────────────────────────────
            # 50% key-column Jaccard  (projection-agnostic)
            # 30% exact row overlap   (rewards full correctness)
            # 20% row count ratio     (soft penalty for very different cardinality)
            score = (jaccard * 0.50) + (exact_overlap * 0.30) + (count_ratio * 0.20)

            return round(max(0.001, min(0.999, score)), 4)

        finally:
            conn.close()