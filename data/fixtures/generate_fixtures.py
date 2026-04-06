#!/usr/bin/env python3
"""
data/fixtures/generate_fixtures.py
Thin wrapper around data/seed_database.py:
  1. Generates the canonical benchmark_seed42.db (SEED=42, 100 000 rows).
  2. Prints a row-count summary.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from data.seed_database import seed_database
import sqlite3


def main():
    db_path = ROOT / "data" / "fixtures" / "benchmark_seed42.db"

    if db_path.exists():
        print(f"Database already exists at {db_path}")
        print("Delete it first if you want to regenerate.")
    else:
        print("Generating benchmark_seed42.db with 100k rows…")
        seed_database(str(db_path), 100_000)

    # Print summary
    conn = sqlite3.connect(str(db_path))
    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    print("\n📊 Row counts:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count:,}")
    conn.close()


if __name__ == "__main__":
    main()
