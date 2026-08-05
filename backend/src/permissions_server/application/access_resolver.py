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
    Resource,
    Restriction,
    Role,
    SystemRole,
    role_rank,
)
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.restriction_repository import RestrictionRepository
from permissions_server.domain.ports.system_role_repository import SystemRoleRepository
from permissions_server.domain.ports.team_repository import TeamRepository


@dataclass(frozen=True, slots=True)
class AccessSnapshot:
    """A user's full grant set, pre-indexed for O(1) lookups. Grants come from
    the user directly AND every team they belong to — highest rank among all
    of them wins at whichever resource they're indexed under."""

    system_roles: frozenset[SystemRole]
    grantees: frozenset[Grantee] = field(default_factory=frozenset)
    grants_by_resource: dict[str, list[PermissionGrant]] = field(default_factory=dict)


class AccessResolver:
    def __init__(
        self,
        resource_repository: ResourceRepository,
        grant_repository: PermissionGrantRepository,
        team_repository: TeamRepository,
        system_role_repository: SystemRoleRepository,
        restriction_repository: RestrictionRepository,
    ) -> None:
        self._resource_repository = resource_repository
        self._grant_repository = grant_repository
        self._team_repository = team_repository
        self._system_role_repository = system_role_repository
        self._restriction_repository = restriction_repository

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
        return AccessSnapshot(
            system_roles=system_roles,
            grantees=frozenset(grantees),
            grants_by_resource=by_resource,
        )

    async def nearest_grants(
        self,
        resource_id: str,
        snapshot: AccessSnapshot,
        *,
        path: list[Resource] | None = None,
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
        once. Pass a precomputed `path` (from path_to_root) to avoid a second
        query when the caller already has it."""
        if path is None:
            path = await self._resource_repository.path_to_root(resource_id)  # root-first
        for node in reversed(path):
            grants_here = snapshot.grants_by_resource.get(node.id)
            if grants_here:
                return node.id, grants_here
            if not node.inherits_from_parent:
                break
        return None

    async def nearest_restriction(
        self,
        resource_id: str,
        *,
        path: list[Resource] | None = None,
    ) -> tuple[str, list[Restriction]] | None:
        """The restriction twin of nearest_grants. Unlike grants, a node is
        gated by the mere existence of ANY restriction entry there —
        regardless of who it names — so this fetches every restriction row
        across the whole ancestor path (not grantee-filtered) and walks
        nearest-first, respecting `inherits_from_parent` the same way
        nearest_grants does."""
        if path is None:
            path = await self._resource_repository.path_to_root(resource_id)
        if not path:
            return None
        rows = await self._restriction_repository.list_restrictions_for_resource_ids(
            [node.id for node in path]
        )
        by_resource: dict[str, list[Restriction]] = {}
        for restriction in rows:
            by_resource.setdefault(restriction.resource_id, []).append(restriction)
        for node in reversed(path):
            entries = by_resource.get(node.id)
            if entries:
                return node.id, entries
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
        """Ties among multiple grants (or restriction entries) at the nearest
        ancestor break by highest rank — never by recency. TODO(open decision,
        unresolved as of 2026-07-29): see CLAUDE.md "Known deferred work" — the
        Hebrew guide (instructions/new-guide-he.txt line 11) asks for recency
        ("last one wins") instead; do not change this without the user's say. Precedence:
        1. SUPER_EDITOR bypasses everything, including restrictions, resolving
           to Role.ADMIN unconditionally.
        2. SUPER_VIEWER also bypasses everything, including restrictions
           (confirmed 2026-07-31 — both system-wide roles are "greater than
           any [resource-level] permission," restrictions included), resolving
           to Role.VIEWER — EXCEPT inside the actor's own personal workspace
           (confirmed 2026-07-31): there they're just a normal Admin via their
           own bootstrap grant, same as anyone else's personal workspace owner,
           not artificially capped by a system role meant to apply everywhere
           ELSE. Resolution falls through to steps 3-4 normally in that case.
        3. A restriction at the nearest ancestor (inclusive) that has any
           restriction row gates access completely: an actor not listed
           there gets None regardless of any grant they hold there or above
           (even an Admin grant); a listed actor gets the highest-rank
           matching entry's role. This fully short-circuits ordinary grant
           resolution below.
        4. Otherwise, today's unchanged nearest-grant resolution.
        Pass a precomputed `snapshot` when resolving many resources for the
        same user (CatalogService does); otherwise pass `user_id` and it's
        fetched here."""
        if snapshot is None:
            assert user_id is not None, "either user_id or snapshot must be provided"
            snapshot = await self.snapshot_for_user(user_id)

        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return Role.ADMIN

        path = await self._resource_repository.path_to_root(resource_id)

        resolved_user_id = user_id or next(
            (g.user_id for g in snapshot.grantees if g.grantee_type is GranteeType.USER), None
        )
        owns_this_personal_workspace = bool(path) and path[0].owner_id == resolved_user_id

        if SystemRole.SUPER_VIEWER in snapshot.system_roles and not owns_this_personal_workspace:
            return Role.VIEWER

        restriction = await self.nearest_restriction(resource_id, path=path)
        if restriction is not None:
            _, entries = restriction
            matching = [e for e in entries if e.grantee in snapshot.grantees]
            if not matching:
                return None
            return max((e.role for e in matching), key=role_rank)

        nearest = await self.nearest_grants(resource_id, snapshot, path=path)
        if nearest is None:
            return None
        _, grants = nearest
        return max((g.role for g in grants), key=role_rank)
