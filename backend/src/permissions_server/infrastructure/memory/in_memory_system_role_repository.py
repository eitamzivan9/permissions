from __future__ import annotations

from permissions_server.domain.entities import SystemRole


class InMemorySystemRoleRepository:
    def __init__(self) -> None:
        self._roles: dict[str, set[SystemRole]] = {}

    async def list_system_roles(self, user_id: str) -> frozenset[SystemRole]:
        return frozenset(self._roles.get(user_id, set()))

    async def grant_system_role(
        self, user_id: str, role: SystemRole, granted_by: str
    ) -> None:
        self._roles.setdefault(user_id, set()).add(role)

    async def revoke_system_role(self, user_id: str, role: SystemRole) -> None:
        self._roles.get(user_id, set()).discard(role)
