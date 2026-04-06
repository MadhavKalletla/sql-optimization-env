# server/graders/speedup_grader.py
"""
Tiered speedup scoring per PDF spec:
  100x → 1.0   |  50x → 0.85  |  20x → 0.70  |  10x → 0.55
   5x → 0.40   |   2x → 0.25  |   1x → 0.10  |  <1x → 0.0
Returns value in [0.0, 1.0].  Weight (0.35) is applied by RewardComposer.
"""


class SpeedupGrader:

    def grade(self, orig_time_ms: float, opt_time_ms: float) -> float:
        # ✅ FIX: prevent division issues / invalid inputs
        if opt_time_ms <= 0 or orig_time_ms <= 0:
            return 0.0

        ratio = orig_time_ms / opt_time_ms

        if ratio >= 100:
            return 1.0
        if ratio >= 50:
            return 0.85
        if ratio >= 20:
            return 0.70
        if ratio >= 10:
            return 0.55
        if ratio >= 5:
            return 0.40
        if ratio >= 2:
            return 0.25
        if ratio >= 1:
            return 0.10

        return 0.0  # Slower than original