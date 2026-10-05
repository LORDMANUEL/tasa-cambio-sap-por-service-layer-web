"""Single source of truth for the Atas application version."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
VERSION_FILE=ROOT/'VERSION.txt'

@lru_cache(maxsize=1)
def get_version() -> str:
    try:
        value=VERSION_FILE.read_text(encoding='utf-8').strip()
        return value or '0.0.0-dev'
    except OSError:
        return '0.0.0-dev'
