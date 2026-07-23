"""The one place effective role is computed. Never re-implement this
resolution logic elsewhere (a router, the frontend) — CatalogService,
PermissionGrantService, and AccessTransparencyService all go through
AccessResolver so they can't drift apart."""

from __future__ import annotations

from dataclasses import dataclass, field

from permissions_server.domain.entities import (
    Grantee,
    GranteeType,
    PermissionGrant,
    Role,
    SystemRole,
    role_rank,
)
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.system_role_repository import SystemRoleRepository
from permissions_server.domain.ports.team_repository import TeamRepository


@dataclass(frozen=True, slots=True)
class AccessSnapshot:
    """A user's full grant set, pre-indexed for O(1) lookups. Grants come from
    the user directly AND every team they belong to — highest rank among all
    of them wins at whichever resource they're indexed under."""

    system_roles: frozenset[SystemRole]
    grants_by_resource: dict[str, list[PermissionGrant]] = field(default_factory=dict)


class AccessResolver:
    def __init__(
        self,
        resource_repository: ResourceRepository,
        grant_repository: PermissionGrantRepository,
        team_repository: TeamRepository,
        system_role_repository: SystemRoleRepository,
    ) -> None:
        self._resource_repository = resource_repository
        self._grant_repository = grant_repository
        self._team_repository = team_repository
        self._system_role_repository = system_role_repository

    async def snapshot_for_user(self, user_id: str) -> AccessSnapshot:
        teams = await self._team_repository.list_teams_for_user(user_id)
        grantees = [Grantee(GranteeType.USER, user_id=user_id)] + [
            Grantee(GranteeType.TEAM, team_id=team.id) for team in teams
        ]
        grants = await self._grant_repository.list_grants_for_grantees(grantees)

        by_resource: dict[str, list[PermissionGrant]] = {}
        for grant in grants:
            by_resource.setdefault(grant.resource_id, []).append(grant)

        system_roles = await self._system_role_repository.list_system_roles(user_id)
        return AccessSnapshot(system_roles=system_roles, grants_by_resource=by_resource)

    async def nearest_grants(
        self, resource_id: str, snapshot: AccessSnapshot
    ) -> tuple[str, list[PermissionGrant]] | None:
        """Walk from resource_id up to the tree root; return
        (origin_resource_id, grants) for the NEAREST ancestor (inclusive)
        with any explicit grant, or None if no ancestor has one. A closer
        override fully replaces a farther one — same 'sticky override'
        semantics as the old layer-vs-map default, generalized to N levels.
        The climb also stops the moment it passes a node whose own
        `inherits_from_parent` is False — that node's own grant (if any) is
        still checked first, but nothing further up ever leaks past it, so a
        single flag can wall off a whole subtree without enumerating every
        grantee. Shared by effective_role and
        AccessTransparencyService.explain_access so this climb exists exactly
        once."""
        path = await self._resource_repository.path_to_root(resource_id)  # root-first
        for node in reversed(path):
            grants_here = snapshot.grants_by_resource.get(node.id)
            if grants_here:
                return node.id, grants_here
            if not node.inherits_from_parent:
                break
        return None

    async def effective_role(
        self,
        resource_id: str,
        *,
        user_id: str | None = None,
        snapshot: AccessSnapshot | None = None,
    ) -> Role | None:
        """Ties among multiple grants at the nearest ancestor (a direct grant
        plus N team grants) break by highest rank. Returns None if no
        ancestor (inclusive) has any grant. Pass a precomputed `snapshot` when
        resolving many resources for the same user (CatalogService does);
        otherwise pass `user_id` and it's fetched here."""
        if snapshot is None:
            assert user_id is not None, "either user_id or snapshot must be provided"
            snapshot = await self.snapshot_for_user(user_id)

        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return Role.ADMIN
        if SystemRole.SUPER_VIEWER in snapshot.system_roles:
            return Role.VIEWER

        nearest = await self.nearest_grants(resource_id, snapshot)
        if nearest is None:
            return None
        _, grants = nearest
        return max((g.role for g in grants), key=role_rank)
