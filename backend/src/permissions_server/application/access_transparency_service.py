"""'Why do I have this access' — one shared breakdown, two thin callers:
my_access (self-service, no gate) and check_access (a manager/admin
inspecting someone else, gated on Manager+ at the resource)."""

from __future__ import annotations

from dataclasses import dataclass

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.domain.entities import (
    AuthenticatedUser,
    Grantee,
    Role,
    SystemRole,
    role_rank,
)
from permissions_server.domain.errors import ForbiddenError


@dataclass(frozen=True, slots=True)
class AccessSource:
    grantee: Grantee | None
    """None when this source is a system-role bypass rather than a grant."""
    system_role: SystemRole | None
    origin_resource_id: str | None
    """The resource this grant actually lives on (may be an ancestor). None
    for a system-role source — it's global, not resource-scoped."""
    role: Role
    is_effective: bool
    """True iff this is the source that actually wins the resolution."""


class AccessTransparencyService:
    def __init__(self, access_resolver: AccessResolver) -> None:
        self._access_resolver = access_resolver

    async def explain_access(
        self, subject_user_id: str, resource_id: str
    ) -> list[AccessSource]:
        snapshot = await self._access_resolver.snapshot_for_user(subject_user_id)
        sources: list[AccessSource] = []

        for system_role in snapshot.system_roles:
            role = Role.ADMIN if system_role is SystemRole.SUPER_EDITOR else Role.VIEWER
            sources.append(
                AccessSource(
                    grantee=None,
                    system_role=system_role,
                    origin_resource_id=None,
                    role=role,
                    is_effective=True,
                )
            )

        nearest = await self._access_resolver.nearest_grants(resource_id, snapshot)
        if nearest is not None:
            origin_resource_id, grants = nearest
            max_rank = max(role_rank(g.role) for g in grants)
            system_role_bypasses = bool(snapshot.system_roles)
            for grant in grants:
                sources.append(
                    AccessSource(
                        grantee=grant.grantee,
                        system_role=None,
                        origin_resource_id=origin_resource_id,
                        role=grant.role,
                        is_effective=not system_role_bypasses
                        and role_rank(grant.role) == max_rank,
                    )
                )

        return sources

    async def my_access(
        self, current_user: AuthenticatedUser, resource_id: str
    ) -> list[AccessSource]:
        return await self.explain_access(current_user.id, resource_id)

    async def check_access(
        self, actor: AuthenticatedUser, subject_user_id: str, resource_id: str
    ) -> list[AccessSource]:
        actor_snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if not actor_snapshot.system_roles:
            actor_role = await self._access_resolver.effective_role(
                resource_id, snapshot=actor_snapshot
            )
            if actor_role is None or role_rank(actor_role) < role_rank(Role.MANAGER):
                raise ForbiddenError(
                    f"{actor.id} may not inspect {subject_user_id}'s access at {resource_id}"
                )
        return await self.explain_access(subject_user_id, resource_id)
