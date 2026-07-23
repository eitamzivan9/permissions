"""Owns the delegation rule end-to-end. Grantee-agnostic: operates on a
Grantee (user or team), not separate code paths per grantee type."""

from __future__ import annotations

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.audit_service import AuditService
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
from permissions_server.domain.ports.user_directory import UserDirectory


class PermissionGrantService:
    def __init__(
        self,
        grant_repository: PermissionGrantRepository,
        access_resolver: AccessResolver,
        org_hierarchy: OrgHierarchy,
        user_directory: UserDirectory,
        audit_service: AuditService,
    ) -> None:
        self._grant_repository = grant_repository
        self._access_resolver = access_resolver
        self._org_hierarchy = org_hierarchy
        self._user_directory = user_directory
        self._audit_service = audit_service

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
        transitive. TEAM grantees skip the org-chart check entirely — a team
        isn't a person in an org chart. SUPER_EDITOR bypasses both checks."""
        snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return True

        actor_role = await self._access_resolver.effective_role(resource_id, snapshot=snapshot)
        if actor_role is None or role_rank(actor_role) < role_rank(Role.MANAGER):
            return False
        if actor_role is Role.MANAGER and role_rank(role_to_grant) >= role_rank(Role.MANAGER):
            return False

        if grantee.grantee_type is GranteeType.TEAM:
            return True

        assert grantee.user_id is not None
        return await self._org_hierarchy.is_manager_of(actor.id, grantee.user_id)

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
        self, actor: AuthenticatedUser
    ) -> list[AuthenticatedUser]:
        subordinate_ids = await self._org_hierarchy.subordinates_of(actor.id)
        users = [await self._user_directory.get_user(uid) for uid in subordinate_ids]
        return [u for u in users if u is not None]
