# server/graders/antipattern_grader.py
"""
Anti-pattern grader — checks pattern identification and explanation quality.
Returns value in [0.0, 1.0].  Weight (0.20) applied by RewardComposer.
"""

from ..models import AntiPatternType, SQLOptAction


class AntiPatternGrader:

    def grade(self, task, action: SQLOptAction) -> float:
        score = 0.0

        expected = task.expected_pattern

        # Safe handling: frontend may send a plain string instead of an enum.
        raw = action.identified_pattern
        if raw is None:
            identified = "NONE"
        elif isinstance(raw, str):
            identified = raw
        else:
            identified = raw.value  # it's an AntiPatternType enum

        # 40 % for correct identification
        if identified == expected:
            score += 0.40
        elif self._is_partial_match(identified, expected):
            score += 0.20

        # 30 % for quality of explanation
        explanation_score = self._grade_explanation(action.explanation, expected)
        score += explanation_score * 0.30

        # 30 % for query actually fixing the pattern
        fix_score = self._grade_fix_quality(task, action)
        score += fix_score * 0.30

        return min(0.999, score)

    def _is_partial_match(self, identified: str, expected: str) -> bool:
        related = {
            "N_PLUS_ONE": ["MISSING_INDEX"],
            "CARTESIAN_PRODUCT": ["MISSING_INDEX"],
            "LEADING_WILDCARD": ["MISSING_INDEX"],
            "UNBOUNDED_AGGREGATION": ["N_PLUS_ONE", "IMPLICIT_CAST"],
        }
        return identified in related.get(expected, [])

    def _grade_explanation(self, explanation: str, expected_pattern: str) -> float:
        if not explanation:
            return 0.001

        # "Manual" means the user chose not to explain — partial credit only.
        if explanation.strip().lower() == "manual":
            return 0.5

        keywords = {
            "N_PLUS_ONE": ["correlated", "subquery", "per row", "n+1", "loop", "join"],
            "CARTESIAN_PRODUCT": ["cartesian", "missing join", "cross product", "condition", "on"],
            "MISSING_INDEX": ["index", "full scan", "indexed", "btree", "create index"],
            "SELECT_STAR": ["select *", "all columns", "unnecessary", "bandwidth", "projection"],
            "LEADING_WILDCARD": ["wildcard", "like %", "full scan", "prefix", "leading"],
            "IMPLICIT_CAST": ["cast", "type", "string", "numeric", "convert", "implicit"],
            "UNBOUNDED_AGGREGATION": ["group by", "no filter", "where", "limit", "aggregat", "unbounded"],
        }

        words = explanation.lower()
        hits = sum(1 for kw in keywords.get(expected_pattern, []) if kw in words)
        return min(0.999, hits / 3)

    def _grade_fix_quality(self, task, action: SQLOptAction) -> float:
        """Check that the optimized query actually addresses the anti-pattern."""
        opt = action.optimized_query.upper()
        pattern = task.expected_pattern

        if pattern == "SELECT_STAR" and "SELECT *" not in opt:
            return 0.999
        if pattern == "N_PLUS_ONE" and "JOIN" in opt:
            return 0.999
        if pattern == "CARTESIAN_PRODUCT" and " ON " in opt:
            return 0.999
        if pattern == "MISSING_INDEX" and action.index_statements:
            return 0.999
        if pattern == "LEADING_WILDCARD" and "LIKE '%" not in opt:
            return 0.8
        if pattern == "IMPLICIT_CAST" and "CAST" not in opt:
            return 0.999
        if pattern == "UNBOUNDED_AGGREGATION" and ("WHERE" in opt or "BETWEEN" in opt):
            return 0.999

        return 0.2  # Partial credit