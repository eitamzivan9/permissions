"""Shared loader for mock_users.json — the single parse point used by both
mock_user_directory.py (identity lookups) and mock_org_hierarchy.py (manager
chains), so the fixture is read once, not reimplemented per consumer."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

_FIXTURE_PATH = Path(__file__).parent / "mock_users.json"


class MockUserRecord(TypedDict):
    id: str
    name: str
    email: str
    manager_id: str | None


@lru_cache
def load_mock_users() -> list[MockUserRecord]:
    with _FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)
