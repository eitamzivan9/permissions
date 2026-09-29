"""Owns setting/revoking restrictions end-to-end — a deliberately separate,
Admin-only power from PermissionGrantService's Manager-or-Admin grant
delegation. Grantee-agnostic, same as PermissionGrantService."""

from __future__ import annotations

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.audit_service import AuditService
from permissions_server.application.delegation_rules import grantee_passes_org_chart_check
from permissions_server.domain.entities import (
    AuthenticatedUser,
    Grantee,
    GranteeType,
    Restriction,
    Role,
    SystemRole,
)
from permissions_server.domain.errors import ConflictError, ForbiddenError
from permissions_server.domain.ports.org_hierarchy import OrgHierarchy
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.restriction_repository import RestrictionRepository


class RestrictionService:
    def __init__(
        self,
        restriction_repository: RestrictionRepository,
        access_resolver: AccessResolver,
        org_hierarchy: OrgHierarchy,
        audit_service: AuditService,
        resource_repository: ResourceRepository,
    ) -> None:
        self._restriction_repository = restriction_repository
        self._access_resolver = access_resolver
        self._org_hierarchy = org_hierarchy
        self._audit_service = audit_service
        self._resource_repository = resource_repository

    async def can_set_restriction(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str
    ) -> bool:
        """Admin-only (NOT Manager, unlike ordinary grants where Manager
        keeps its existing Editor/Viewer-only grant power unchanged).
        effective_role is already restriction-aware, so this naturally
        respects a restriction ALREADY on this resource — including one that
        already excludes the actor — with no special-case code needed."""
        snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if SystemRole.SUPER_EDITOR in snapshot.system_roles:
            return True

        actor_role = await self._access_resolver.effective_role(resource_id, snapshot=snapshot)
        if actor_role is not Role.ADMIN:
            return False

        return await grantee_passes_org_chart_check(
            self._org_hierarchy, self._resource_repository, actor.id, grantee, resource_id
        )

    async def set_restriction(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> Restriction:
        if not await self.can_set_restriction(actor, grantee, resource_id):
            raise ForbiddenError(
                f"{actor.id} may not restrict {resource_id} for {grantee}"
            )
        # Computed before the upsert below, so a resource with zero
        # restriction rows today is recognized as "first restriction" even
        # though we're about to write one.
        is_first_restriction = not await self._restriction_repository.list_restrictions_for_resource(
            resource_id
        )

        existing = await self._restriction_repository.get_restriction(grantee, resource_id)
        result = await self._restriction_repository.upsert_restriction(
            grantee, resource_id, role, granted_by=actor.id
        )
        if existing is None:
            await self._audit_service.record_restrict(actor, grantee, resource_id, role)
        elif existing.role != role:
            await self._audit_service.record_restriction_role_change(
                actor, grantee, resource_id, role
            )

        # Whitelisting anyone at all on a resource that had no restriction
        # before now gates that resource completely (see AccessResolver's
        # nearest_restriction precedence) — without this, the acting admin
        # could lock themselves out with their very first restriction. Skip
        # if they already explicitly whitelisted themselves in this same call.
        actor_grantee = Grantee(GranteeType.USER, user_id=actor.id)
        if is_first_restriction and grantee != actor_grantee:
            await self._restriction_repository.upsert_restriction(
                actor_grantee, resource_id, Role.ADMIN, granted_by=actor.id
            )
            await self._audit_service.record_restrict(actor, actor_grantee, resource_id, Role.ADMIN)

        return result

    async def revoke_restriction(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str
    ) -> None:
        existing = await self._restriction_repository.get_restriction(grantee, resource_id)
        if existing is None:
            return
        if not await self.can_set_restriction(actor, grantee, resource_id):
            raise ForbiddenError(
                f"{actor.id} may not unrestrict {resource_id} for {grantee}"
            )

        if existing.role is Role.ADMIN:
            all_restrictions = await self._restriction_repository.list_restrictions_for_resource(
                resource_id
            )
            remaining = [r for r in all_restrictions if r.grantee != grantee]
            remaining_admins = [r for r in remaining if r.role is Role.ADMIN]
            # Only a problem if the resource STAYS gated afterward (other
            # restriction rows remain) with zero admins left to manage it.
            # Removing the very last restriction row entirely — even an
            # Admin-role one — is always fine: that's a full unrestrict, not
            # an orphan, and "Clear all" needs to be able to reach zero.
            if remaining and not remaining_admins:
                raise ConflictError(
                    f"cannot remove the last Admin-role restriction entry on {resource_id} "
                    "while other restriction entries remain — it would leave the resource "
                    "gated with no one able to manage its whitelist",
                    code="last_admin_restriction",
                )

        await self._restriction_repository.delete_restriction(grantee, resource_id)
        await self._audit_service.record_unrestrict(actor, grantee, resource_id, existing.role)
