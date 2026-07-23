"""Kept separate from PermissionGrantRepository on purpose: system roles have
no resource_id and a different (admin-only) assignment lifecycle — mixing them
into grant rows would force every grant consumer to handle a nullable-resource
case."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import SystemRole


class SystemRoleRepository(Protocol):
    async def list_system_roles(self, user_id: str) -> frozenset[SystemRole]: ...

    async def grant_system_role(
        self, user_id: str, role: SystemRole, granted_by: str
    ) -> None: ...

    async def revoke_system_role(self, user_id: str, role: SystemRole) -> None: ...
