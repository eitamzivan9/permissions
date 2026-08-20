"""Who manages whom — backs the org-chart delegation check on user grantees."""

from __future__ import annotations

from typing import Protocol


class OrgHierarchy(Protocol):
    """Manager-chain lookups the delegation rule depends on. Both methods are
    transitive (a manager's manager's report still counts), not just direct reports."""

    async def is_manager_of(self, manager_id: str, subject_id: str) -> bool: ...

    async def subordinates_of(self, manager_id: str) -> list[str]: ...
