"""Records grant/revoke actions append-only. Kept as a collaborator that
PermissionGrantService calls, not inlined into its grant/revoke logic —
audit-recording is a separate reason to change from grant-authorization."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from permissions_server.domain.entities import (
    AuditAction,
    AuditLogEntry,
    AuthenticatedUser,
    Grantee,
    Role,
)
from permissions_server.domain.ports.audit_log_repository import AuditLogRepository
from permissions_server.domain.ports.entity_repository import Page


class AuditService:
    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def record_grant(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        return await self._record(actor, grantee, resource_id, role, AuditAction.GRANT)

    async def record_revoke(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        return await self._record(actor, grantee, resource_id, role, AuditAction.REVOKE)

    async def record_role_change(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        """`role` is the NEW role the grantee ends up with."""
        return await self._record(actor, grantee, resource_id, role, AuditAction.ROLE_CHANGE)

    async def record_restrict(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        return await self._record(actor, grantee, resource_id, role, AuditAction.RESTRICT)

    async def record_unrestrict(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        return await self._record(actor, grantee, resource_id, role, AuditAction.UNRESTRICT)

    async def record_restriction_role_change(
        self, actor: AuthenticatedUser, grantee: Grantee, resource_id: str, role: Role
    ) -> AuditLogEntry:
        """`role` is the NEW role the restriction entry ends up with."""
        return await self._record(
            actor, grantee, resource_id, role, AuditAction.RESTRICTION_ROLE_CHANGE
        )

    async def _record(
        self,
        actor: AuthenticatedUser,
        grantee: Grantee,
        resource_id: str,
        role: Role,
        action: AuditAction,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=uuid4().hex,
            actor_id=actor.id,
            grantee=grantee,
            resource_id=resource_id,
            role=role,
            action=action,
            timestamp=datetime.now(timezone.utc),
        )
        await self._audit_log_repository.append(entry)
        return entry

    async def history_for_resource(
        self, resource_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        return await self._audit_log_repository.list_for_resource(
            resource_id, page=page, page_size=page_size
        )

    async def history_for_actor(
        self, actor_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        return await self._audit_log_repository.list_for_actor(
            actor_id, page=page, page_size=page_size
        )
