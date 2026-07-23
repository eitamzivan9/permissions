from __future__ import annotations

from uuid import uuid4

from permissions_server.domain.entities import Team
from permissions_server.infrastructure.memory.in_memory_entity_repository import (
    InMemoryEntityRepository,
)
from permissions_server.infrastructure.seed_data import TEAM_MEMBERSHIPS, TEAMS


class InMemoryTeamRepository(InMemoryEntityRepository[Team]):
    def __init__(self) -> None:
        super().__init__(TEAMS)
        self._members: dict[str, set[str]] = {
            team_id: set(user_ids) for team_id, user_ids in TEAM_MEMBERSHIPS.items()
        }

    async def list_members(self, team_id: str) -> list[str]:
        return sorted(self._members.get(team_id, set()))

    async def list_teams_for_user(self, user_id: str) -> list[Team]:
        return [
            self._by_id[team_id]
            for team_id, members in self._members.items()
            if user_id in members and team_id in self._by_id
        ]

    async def add_member(self, team_id: str, user_id: str) -> None:
        self._members.setdefault(team_id, set()).add(user_id)

    async def remove_member(self, team_id: str, user_id: str) -> None:
        self._members.get(team_id, set()).discard(user_id)

    async def create(self, name: str) -> Team:
        team = Team(id=uuid4().hex, name=name)
        self._by_id[team.id] = team
        self._members[team.id] = set()
        return team
