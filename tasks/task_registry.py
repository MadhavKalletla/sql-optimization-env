# tasks/task_registry.py

import random

from tasks.easy.gst_missing_index import TASK as T_E1
from tasks.easy.pds_select_star import TASK as T_E2
from tasks.easy.railway_simple_filter import TASK as T_E3

from tasks.medium.gst_n_plus_one import TASK as T_M1
from tasks.medium.pds_cartesian import TASK as T_M2
from tasks.medium.mgnrega_wildcard import TASK as T_M3

from tasks.hard.gst_multi_join import TASK as T_H1
from tasks.hard.railway_tatkal_workload import TASK as T_H2
from tasks.hard.mgnrega_schema_e import TASK as T_H3
from tasks.easy.mgnrega_count import TASK as T_E4
from tasks.medium.railway_missing_index import TASK as T_M4
from tasks.medium.gst_unbounded_aggregation import TASK as T_M5
from tasks.hard.pds_n_plus_one import TASK as T_H4
from tasks.hard.mgnrega_implicit_cast import TASK as T_H5


LEVEL_TASKS = {
    1: [T_E2, T_E4],            # Intro: SELECT* tasks (2 tasks)
    2: [T_E1, T_E3, T_M4, T_M5], # Easy: missing index + aggregation (4 tasks)
    3: [T_M1, T_M2, T_M3],      # Medium: N+1, Cartesian, wildcard (3 tasks)
    4: [T_H1, T_H2, T_H4, T_H5], # Hard: multi-pattern (4 tasks)
    5: [T_H3],                  # Expert: schema-level
}


class TaskRegistry:

    def get_task_for_level(self, level: int, seed: int = None):
        tasks = LEVEL_TASKS.get(level, LEVEL_TASKS[1])

        # ✅ FIX: deterministic randomness (no global seed pollution)
        if seed is not None:
            rng = random.Random(seed)
            return rng.choice(tasks)

        return random.choice(tasks)

    def get_task_by_id(self, task_id: str):
        all_tasks = [t for tasks in LEVEL_TASKS.values() for t in tasks]
        return next((t for t in all_tasks if t.task_id == task_id), None)

    def all_tasks(self):
        return [t for tasks in LEVEL_TASKS.values() for t in tasks]

    def get_all_tasks(self):
        """Unique tasks across all curriculum levels."""
        by_id = {}
        for tasks in LEVEL_TASKS.values():
            for t in tasks:
                by_id[t.task_id] = t
        return list(by_id.values())