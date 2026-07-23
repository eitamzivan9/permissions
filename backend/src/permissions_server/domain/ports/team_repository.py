from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import Team
from permissions_server.domain.ports.entity_repository import EntityRepository


class TeamRepository(EntityRepository[Team], Protocol):
    """Team identity (get/list/search) reuses EntityRepository, same as
    ResourceRepository — both are just an id+name shape. Membership below is
    separate, mutable state."""

    async def list_members(self, team_id: str) -> list[str]: ...

    async def list_teams_for_user(self, user_id: str) -> list[Team]:
        """Every team this user belongs to — the reverse index AccessResolver
        needs to know which team-grantees might apply for a user."""
        ...

    async def add_member(self, team_id: str, user_id: str) -> None: ...

    async def remove_member(self, team_id: str, user_id: str) -> None: ...

    async def create(self, name: str) -> Team: ...
