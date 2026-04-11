# server/graders/index_grader.py
"""
Index grader — evaluates whether submitted indexes improve the execution plan.
Returns value in [0.0, 1.0].  Weight (0.10) applied by RewardComposer.
"""


class IndexGrader:

    def grade(self, task, action, opt_plan) -> float:
        if not action.index_statements:
            # No indexes submitted — partial credit if pattern doesn't need one
            if task.expected_pattern in ("SELECT_STAR", "LEADING_WILDCARD"):
                return 0.5
            return 0.001

        score = 0.001

        # Check 1: Was an index actually used in the plan?  (60 %)
        if opt_plan and opt_plan.using_index:
            score += 0.60

        # Check 2: Do indexed columns appear in the WHERE clause?  (20 %)
        query_lower = action.optimized_query.lower()

        for stmt in action.index_statements:
            try:  # ✅ FIX: prevent crash on malformed SQL
                stmt_lower = stmt.lower()

                if "(" in stmt_lower and ")" in stmt_lower:
                    cols_part = stmt_lower[
                        stmt_lower.index("(") + 1 : stmt_lower.rindex(")")
                    ]
                    indexed_cols = [c.strip() for c in cols_part.split(",")]

                    if any(col in query_lower for col in indexed_cols):
                        score += 0.20
                        break  # Only award once
            except Exception:
                continue  # skip invalid statements safely

        # Check 3: Reasonable number of indexes (20 %)
        n = len(action.index_statements)
        if 1 <= n <= 3:
            score += 0.20
        elif n <= 5:
            score += 0.10
        # >5 is handled by hack detector

        return max(0.001, min(0.999, score))