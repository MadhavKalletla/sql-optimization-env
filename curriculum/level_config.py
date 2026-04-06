# curriculum/level_config.py

LEVEL_CONFIG = {
    1: {"tables": 1, "rows": 10_000,    "patterns": 1, "hint": True,  "label": "Intro"},
    2: {"tables": 2, "rows": 100_000,   "patterns": 1, "hint": True,  "label": "Easy"},
    3: {"tables": 3, "rows": 500_000,   "patterns": 2, "hint": False, "label": "Medium"},
    4: {"tables": 4, "rows": 2_000_000, "patterns": 3, "hint": False, "label": "Hard"},
    5: {"tables": 6, "rows": 5_000_000, "patterns": 4, "hint": False, "label": "Expert"},
}
