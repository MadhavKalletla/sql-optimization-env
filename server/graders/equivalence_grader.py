# server/graders/equivalence_grader.py
"""
Equivalence grader — Jaccard similarity (70 %) + row-count ratio (30 %).
Returns value in [0.0, 1.0].  Weight (0.25) applied by RewardComposer.

FIX: Uses absolute DB path passed from environment, not a module-level relative.
"""

import sqlite3
from pathlib import Path

# Fallback — overridden at call site
_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB = _ROOT / "data" / "fixtures" / "benchmark_seed42.db"


class EquivalenceGrader:

    def grade(self, task, optimized_query: str, db_path: Path = None) -> float:
        db = db_path or _DEFAULT_DB
        conn = sqlite3.connect(str(db))

        try:
            original_rows = list(
                map(tuple, conn.execute(task.slow_query).fetchall())
            )

            try:
                opt_rows = list(
                    map(tuple, conn.execute(optimized_query).fetchall())
                )
            except Exception:
                return 0.0  # Syntax error

            # ✅ STRICT CHECK (FIX ADDED)
            if len(original_rows) != len(opt_rows):
                return 0.0

            original_set = set(original_rows)
            opt_set = set(opt_rows)

            if not original_set:
                return 1.0 if not opt_set else 0.5

            # Jaccard similarity
            intersection = len(original_set & opt_set)
            union = len(original_set | opt_set)

            if union == 0:
                return 1.0

            jaccard = intersection / union

            # Row-count ratio
            count_ratio = min(len(original_rows), len(opt_rows)) / max(
                len(original_rows), len(opt_rows), 1
            )

            return round(jaccard * 0.7 + count_ratio * 0.3, 4)

        finally:
            conn.close()