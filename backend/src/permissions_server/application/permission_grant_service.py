"""Owns the delegation rule end-to-end. Grantee-agnostic: operates on a
Grantee (user or team), not separate code paths per grantee type."""

from __future__ import annotations

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.audit_service import AuditService
from permissions_server.application.delegation_rules import (
    grantee_passes_org_chart_check,
    is_within_actors_personal_workspace,
)
from permissions_server.domain.entities import (
    AuthenticatedUser,
    Grantee,
    GranteeType,
    PermissionGrant,
    Role,
    SystemRole,
    role_rank,
)
from permissions_server.domain.errors import ForbiddenError
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.org_hierarchy import OrgHierarchy
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.user_directory import UserDirectory


class PermissionGrantService:
    def __init__(
        self,
        grant_repository: PermissionGrantRepository,
        access_resolver: AccessResolver,
        org_hierarchy: OrgHierarchy,
        user_directory: UserDirectory,
        audit_service: AuditService,
        resource_repository: ResourceRepository,
    ) -> None:
        self._grant_repository = grant_repository
        self._access_resolver = access_resolver
        self._org_hierarchy = org_hierarchy
        self._user_directory = user_directory
        self._audit_service = audit_service
        self._resource_repository = resource_repository

    async def can_manage(
        self,
        actor: AuthenticatedUser,
        grantee: Grantee,
        resource_id: str,
        role_to_grant: Role,
    ) -> bool:
        """Role-rank rule (both grantee types): actor needs Role.MANAGER+ on
        resource_id; ADMIN may grant/revoke anything, MANAGER may only
        grant/revoke EDITOR/VIEWER (never MANAGER/ADMIN). Delegation rule
        (this project's own synthesis, USER grantees only): additionally
        requires org_hierarchy.is_manager_of(actor, grantee.user_id),
        transitive — unless resource_id is within the actor's own personal
        workspace, where the owner may grant to anyone. TEAM grantees skip
        the org-chart check entirely — a team isn't a person in an org
        chart. SUPER_EDITOR bypasses both checks."""
        snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return True

        actor_role = await self._access_resolver.effective_role(resource_id, snapshot=snapshot)
        if actor_role is None or role_rank(actor_role) < role_rank(Role.MANAGER):
            return False
        if actor_role is Role.MANAGER and role_rank(role_to_grant) >= role_rank(Role.MANAGER):
            return False

        return await grantee_passes_org_chart_check(
            self._org_hierarchy, self._resource_repository, actor.id, grantee, resource_id
        )

    async def grant(
        self,
        actor: AuthenticatedUser,
        grantee: Grantee,
        resource_id: str,
        role: Role,
    ) -> PermissionGrant:
        if not await self.can_manage(actor, grantee, resource_id, role):
            raise ForbiddenError(
                f"{actor.id} may not grant {role.value} on {resource_id} to {grantee}"
            )
        existing = await self._grant_repository.get_grant(grantee, resource_id)
        result = await self._grant_repository.upsert_grant(
            grantee, resource_id, role, granted_by=actor.id
        )
        if existing is None:
            await self._audit_service.record_grant(actor, grantee, resource_id, role)
        elif existing.role != role:
            await self._audit_service.record_role_change(actor, grantee, resource_id, role)
        return result

    async def revoke(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str
    ) -> None:
        existing = await self._grant_repository.get_grant(grantee, resource_id)
        if existing is None:
            return
        if not await self.can_manage(actor, grantee, resource_id, existing.role):
            raise ForbiddenError(
                f"{actor.id} may not revoke {grantee}'s access to {resource_id}"
            )
        await self._grant_repository.delete_grant(grantee, resource_id)
        await self._audit_service.record_revoke(actor, grantee, resource_id, existing.role)

    async def list_manageable_users(
        self, actor: AuthenticatedUser, *, resource_id: str | None = None
    ) -> list[AuthenticatedUser]:
        """Normally just the actor's org-chart subordinates — the only users
        they could actually grant access to (see can_manage). Two cases widen
        that to everyone, both mirroring bypasses can_manage already grants:
        SUPER_EDITOR (bypasses the org-chart check entirely, same as
        can_manage's first check), and resource_id being inside the actor's
        own personal workspace (the owner may grant to anyone there). Without
        this, the picker could show "no one available" for an actor who can
        actually grant to anyone — a real gap found via manual UI testing."""
        snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return await self._user_directory.list_users()
        if resource_id is not None and await is_within_actors_personal_workspace(
            self._resource_repository, actor.id, resource_id
        ):
            return await self._user_directory.list_users()
        subordinate_ids = await self._org_hierarchy.subordinates_of(actor.id)
        users = [await self._user_directory.get_user(uid) for uid in subordinate_ids]
        return [u for u in users if u is not None]

    async def bootstrap_admin_grant(
        self, actor: AuthenticatedUser, target_user_id: str, resource_id: str
    ) -> PermissionGrant:
        """Unconditional Admin grant for target_user_id on a BRAND-NEW
        resource — no other admin can exist there yet, so can_manage's
        delegation check is inapplicable, not merely bypassed by privilege.
        `actor` is recorded as granted_by (the creator, or the superuser who
        designated target_user_id); target_user_id is who actually ends up
        Admin. Still goes through the normal upsert + audit path. Used by
        ResourceService for every creation flow (self-creation and
        superuser-assigned team-workspace admins alike) so the write/audit
        logic exists exactly once."""
        grantee = Grantee(GranteeType.USER, user_id=target_user_id)
        existing = await self._grant_repository.get_grant(grantee, resource_id)
        result = await self._grant_repository.upsert_grant(
            grantee, resource_id, Role.ADMIN, granted_by=actor.id
        )
        if existing is None:
            await self._audit_service.record_grant(actor, grantee, resource_id, Role.ADMIN)
        elif existing.role != Role.ADMIN:
            await self._audit_service.record_role_change(actor, grantee, resource_id, Role.ADMIN)
        return result
