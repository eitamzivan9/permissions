"""Read-only endpoints over the append-only audit log."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from permissions_server.api.deps import (
    get_access_resolver,
    get_audit_service,
    get_current_user,
)
from permissions_server.api.schemas.audit_schemas import AuditLogEntryOut, AuditLogPageOut
from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.audit_service import AuditService
from permissions_server.domain.entities import AuditLogEntry, AuthenticatedUser, Role, role_rank
from permissions_server.domain.errors import ForbiddenError

router = APIRouter(prefix="/audit", tags=["audit"])


def _to_out(entry: AuditLogEntry) -> AuditLogEntryOut:
    return AuditLogEntryOut(
        id=entry.id,
        actor_id=entry.actor_id,
        grantee_type=entry.grantee.grantee_type.value,
        user_id=entry.grantee.user_id,
        team_id=entry.grantee.team_id,
        resource_id=entry.resource_id,
        role=entry.role,
        action=entry.action,
        timestamp=entry.timestamp,
    )


@router.get(
    "/resource/{resource_id}",
    response_model=AuditLogPageOut,
    summary="Audit history for a resource",
    description=(
        "Every GRANT/ROLE_CHANGE/REVOKE (and RESTRICT/UNRESTRICT/"
        "RESTRICTION_ROLE_CHANGE) event ever recorded on this resource, newest "
        "first. Requires Manager+ effective_role at the resource (or a system role) "
        "— 403 otherwise."
    ),
)
async def audit_for_resource(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditLogPageOut:
    snapshot = await access_resolver.snapshot_for_user(current_user.id)
    if not snapshot.system_roles:
        actor_role = await access_resolver.effective_role(resource_id, snapshot=snapshot)
        if actor_role is None or role_rank(actor_role) < role_rank(Role.MANAGER):
            raise ForbiddenError(
                f"{current_user.id} may not view audit history for {resource_id}"
            )
    result = await audit_service.history_for_resource(resource_id, page=page, page_size=page_size)
    return AuditLogPageOut(
        items=[_to_out(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/actor/{actor_id}",
    response_model=AuditLogPageOut,
    summary="Audit history for actions taken BY a user",
    description=(
        "Every audit entry where `actor_id` is the one who took the action, newest "
        "first. Always allowed for the caller's own actor_id; inspecting someone "
        "else's requires a system role — 403 otherwise."
    ),
)
async def audit_for_actor(
    actor_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditLogPageOut:
    if actor_id != current_user.id:
        snapshot = await access_resolver.snapshot_for_user(current_user.id)
        if not snapshot.system_roles:
            raise ForbiddenError(f"{current_user.id} may not view {actor_id}'s audit history")
    result = await audit_service.history_for_actor(actor_id, page=page, page_size=page_size)
    return AuditLogPageOut(
        items=[_to_out(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )
