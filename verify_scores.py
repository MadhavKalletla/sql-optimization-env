#!/usr/bin/env python3
"""
Verification script to ensure all scores are strictly between 0.01 and 0.99
"""

from server.graders.speedup_grader import SpeedupGrader
from server.graders.equivalence_grader import EquivalenceGrader
from server.graders.antipattern_grader import AntiPatternGrader
from server.graders.index_grader import IndexGrader
from server.reward import RewardComposer

def test_speedup_grader():
    grader = SpeedupGrader()
    
    # Test various scenarios
    scores = [
        grader.grade(100, 2, None, None, None),  # Good speedup
        grader.grade(1, 1, None, None, None),    # No speedup, both fast
        grader.grade(100, 100, None, None, None), # No speedup
    ]
    
    for score in scores:
        assert 0.01 <= score <= 0.99, f"SpeedupGrader returned {score}, must be in (0.01, 0.99)"
    
    print("✅ SpeedupGrader: All scores in valid range")

def test_equivalence_grader():
    # This would need a real DB, so we just verify the _clamp function exists
    from server.graders.equivalence_grader import _clamp
    
    test_values = [0.0, 0.001, 0.5, 0.999, 1.0, 1.5, -0.5]
    for val in test_values:
        result = _clamp(val)
        assert 0.01 <= result <= 0.99, f"EquivalenceGrader _clamp({val}) = {result}, must be in (0.01, 0.99)"
    
    print("✅ EquivalenceGrader: _clamp function works correctly")

def test_antipattern_grader():
    from server.graders.antipattern_grader import _clamp
    
    test_values = [0.0, 0.001, 0.5, 0.999, 1.0, 1.5, -0.5]
    for val in test_values:
        result = _clamp(val)
        assert 0.01 <= result <= 0.99, f"AntiPatternGrader _clamp({val}) = {result}, must be in (0.01, 0.99)"
    
    print("✅ AntiPatternGrader: _clamp function works correctly")

def test_index_grader():
    from server.graders.index_grader import _clamp
    
    test_values = [0.0, 0.001, 0.5, 0.999, 1.0, 1.5, -0.5]
    for val in test_values:
        result = _clamp(val)
        assert 0.01 <= result <= 0.99, f"IndexGrader _clamp({val}) = {result}, must be in (0.01, 0.99)"
    
    print("✅ IndexGrader: _clamp function works correctly")

def test_reward_composer():
    from server.reward import _safe
    
    test_values = [0.0, 0.001, 0.5, 0.989, 1.0, 1.5, -0.5]
    for val in test_values:
        result = _safe(val)
        assert 0.011 <= result <= 0.989, f"RewardComposer _safe({val}) = {result}, must be in (0.011, 0.989)"
    
    print("✅ RewardComposer: _safe function works correctly")

if __name__ == "__main__":
    print("Testing score clamping functions...\n")
    
    test_speedup_grader()
    test_equivalence_grader()
    test_antipattern_grader()
    test_index_grader()
    test_reward_composer()
    
    print("\n✅ All tests passed! Scores are properly clamped to (0.01, 0.99)")
