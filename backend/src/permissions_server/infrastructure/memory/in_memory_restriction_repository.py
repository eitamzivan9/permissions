from __future__ import annotations

from permissions_server.domain.entities import Grantee, Restriction, Role

_RestrictionKey = tuple[Grantee, str]


class InMemoryRestrictionRepository:
    def __init__(self) -> None:
        self._restrictions: dict[_RestrictionKey, Restriction] = {}

    @staticmethod
    def _key(grantee: Grantee, resource_id: str) -> _RestrictionKey:
        return (grantee, resource_id)

    async def get_restriction(self, grantee: Grantee, resource_id: str) -> Restriction | None:
        return self._restrictions.get(self._key(grantee, resource_id))

    async def list_restrictions_for_resource(self, resource_id: str) -> list[Restriction]:
        return [r for r in self._restrictions.values() if r.resource_id == resource_id]

    async def list_restrictions_for_resource_ids(
        self, resource_ids: list[str]
    ) -> list[Restriction]:
        ids = set(resource_ids)
        return [r for r in self._restrictions.values() if r.resource_id in ids]

    async def list_restrictions_for_grantees(
        self, grantees: list[Grantee]
    ) -> list[Restriction]:
        grantee_set = set(grantees)
        return [r for r in self._restrictions.values() if r.grantee in grantee_set]

    async def upsert_restriction(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> Restriction:
        restriction = Restriction(
            grantee=grantee, resource_id=resource_id, role=role, granted_by=granted_by
        )
        self._restrictions[self._key(grantee, resource_id)] = restriction
        return restriction

    async def delete_restriction(self, grantee: Grantee, resource_id: str) -> None:
        self._restrictions.pop(self._key(grantee, resource_id), None)

    async def delete_restrictions_for_resource_ids(self, resource_ids: list[str]) -> None:
        ids = set(resource_ids)
        for key, restriction in list(self._restrictions.items()):
            if restriction.resource_id in ids:
                del self._restrictions[key]
