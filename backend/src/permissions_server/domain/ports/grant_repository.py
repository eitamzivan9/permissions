from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import Grantee, PermissionGrant, Role


class PermissionGrantRepository(Protocol):
    async def get_grant(self, grantee: Grantee, resource_id: str) -> PermissionGrant | None:
        """The explicit grant row for this exact (grantee, resource), or None."""
        ...

    async def list_grants_for_resource(self, resource_id: str) -> list[PermissionGrant]:
        """Every explicit grant (any grantee) directly on this resource —
        drives 'who already has access here' views (grant UI, transparency)."""
        ...

    async def list_grants_for_grantees(
        self, grantees: list[Grantee]
    ) -> list[PermissionGrant]:
        """Every explicit grant across ALL resources, for a set of grantees (a
        user + every team they belong to). Inheritance means any ancestor's
        grant can matter, not just grants on one resource — this is the bulk
        fetch AccessResolver.snapshot_for_user needs."""
        ...

    async def upsert_grant(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> PermissionGrant:
        """Set/replace the grant for (grantee, resource)."""
        ...

    async def delete_grant(self, grantee: Grantee, resource_id: str) -> None:
        """Remove the explicit grant row; no error if it didn't exist."""
        ...
