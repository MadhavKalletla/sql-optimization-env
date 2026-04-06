# tasks/_schema_loader.py
"""
Centralised schema file loader — always uses absolute paths
so tasks work regardless of CWD.
"""

from pathlib import Path

_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "data" / "schemas"


def load_schema(filename: str) -> str:
    """Return the DDL text for *filename*, or an inline fallback."""
    path = _SCHEMA_DIR / filename
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"-- Schema file not found: {filename}\n"
