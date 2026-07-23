from __future__ import annotations

from permissions_server.domain.entities import Grantee, PermissionGrant, Role

_GrantKey = tuple[Grantee, str]


class InMemoryGrantRepository:
    def __init__(self) -> None:
        self._grants: dict[_GrantKey, PermissionGrant] = {}

    @staticmethod
    def _key(grantee: Grantee, resource_id: str) -> _GrantKey:
        return (grantee, resource_id)

    async def get_grant(self, grantee: Grantee, resource_id: str) -> PermissionGrant | None:
        return self._grants.get(self._key(grantee, resource_id))

    async def list_grants_for_resource(self, resource_id: str) -> list[PermissionGrant]:
        return [g for g in self._grants.values() if g.resource_id == resource_id]

    async def list_grants_for_grantees(
        self, grantees: list[Grantee]
    ) -> list[PermissionGrant]:
        grantee_set = set(grantees)
        return [g for g in self._grants.values() if g.grantee in grantee_set]

    async def upsert_grant(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> PermissionGrant:
        grant = PermissionGrant(
            grantee=grantee, resource_id=resource_id, role=role, granted_by=granted_by
        )
        self._grants[self._key(grantee, resource_id)] = grant
        return grant

    async def delete_grant(self, grantee: Grantee, resource_id: str) -> None:
        self._grants.pop(self._key(grantee, resource_id), None)
