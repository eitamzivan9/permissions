"""Storage contract for the restriction whitelist gate — the twin of grant_repository.py."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import Grantee, Restriction, Role


class RestrictionRepository(Protocol):
    async def get_restriction(self, grantee: Grantee, resource_id: str) -> Restriction | None:
        """The explicit restriction row for this exact (grantee, resource), or None."""
        ...

    async def list_restrictions_for_resource(self, resource_id: str) -> list[Restriction]:
        """Every restriction entry (any grantee) directly on this resource —
        drives 'who is whitelisted here' views."""
        ...

    async def list_restrictions_for_resource_ids(
        self, resource_ids: list[str]
    ) -> list[Restriction]:
        """Every restriction entry (any grantee) across a SET of resource ids.
        Unlike grants, gating depends on whether ANY entry exists at an
        ancestor node — not just ones naming the current actor — so this
        cannot be grantee-filtered the way list_grants_for_grantees is. This
        is the bulk fetch AccessResolver.nearest_restriction needs to walk an
        ancestor path in one query instead of one per node."""
        ...

    async def list_restrictions_for_grantees(
        self, grantees: list[Grantee]
    ) -> list[Restriction]:
        """Every restriction entry across ALL resources, for a set of
        grantees (a user + every team they belong to) — feeds
        AccessResolver.access_anchor_ids, which the catalog uses to find
        everything the caller can reach without scanning the whole tree."""
        ...

    async def upsert_restriction(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> Restriction:
        """Set/replace the restriction entry for (grantee, resource)."""
        ...

    async def delete_restriction(self, grantee: Grantee, resource_id: str) -> None:
        """Remove the explicit restriction row; no error if it didn't exist."""
        ...

    async def delete_restrictions_for_resource_ids(self, resource_ids: list[str]) -> None:
        """Remove every restriction (any grantee) on any of these resources —
        the cascade cleanup ResourceService.delete() needs before it can drop
        the resource rows themselves."""
        ...
