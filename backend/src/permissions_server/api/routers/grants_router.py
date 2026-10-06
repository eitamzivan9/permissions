"""Per-resource role grants for a user or team grantee."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from permissions_server.api.deps import (
    get_current_user,
    get_grant_repository,
    get_permission_grant_service,
    get_resource_repository,
)
from permissions_server.api.schemas.auth_schemas import MockUserOut
from permissions_server.api.schemas.grant_schemas import GrantOut, SetGrantRequest
from permissions_server.application.permission_grant_service import PermissionGrantService
from permissions_server.domain.entities import AuthenticatedUser, Grantee, GranteeType, PermissionGrant
from permissions_server.domain.errors import NotFoundError
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.resource_repository import ResourceRepository

router = APIRouter(prefix="/grants", tags=["grants"])

GranteeTypePath = Literal["user", "team"]


def _to_grantee(grantee_type: GranteeTypePath, grantee_id: str) -> Grantee:
    if grantee_type == "user":
        return Grantee(GranteeType.USER, user_id=grantee_id)
    return Grantee(GranteeType.TEAM, team_id=grantee_id)


def _to_out(grant: PermissionGrant) -> GrantOut:
    return GrantOut(
        grantee_type=grant.grantee.grantee_type.value,
        user_id=grant.grantee.user_id,
        team_id=grant.grantee.team_id,
        resource_id=grant.resource_id,
        role=grant.role,
        granted_by=grant.granted_by,
    )


async def _ensure_resource_exists(
    resource_id: str, resource_repository: ResourceRepository
) -> None:
    if await resource_repository.get_by_id(resource_id) is None:
        raise NotFoundError(f"no resource with id {resource_id}")


@router.get(
    "/manageable-users",
    response_model=list[MockUserOut],
    summary="List users the caller may grant/restrict",
    description=(
        "Users the caller is transitively above in the org chart (see the "
        "delegation rule) — or, when `resource_id` falls inside the caller's own "
        "personal workspace, every user (the personal-workspace delegation bypass). "
        "`resource_id` is optional; omit it for the org-chart-only list."
    ),
)
async def list_manageable_users(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    permission_grant_service: Annotated[
        PermissionGrantService, Depends(get_permission_grant_service)
    ],
    resource_id: str | None = None,
) -> list[MockUserOut]:
    users = await permission_grant_service.list_manageable_users(
        current_user, resource_id=resource_id
    )
    return [MockUserOut(id=u.id, name=u.name, email=u.email) for u in users]


@router.get(
    "/{resource_id}",
    response_model=list[GrantOut],
    summary="List explicit grants directly on a resource",
    description=(
        "Every explicit grant (any grantee) directly on this resource — not "
        "inherited ones from ancestors. Drives the 'who already has access here' "
        "list in the Manage Access UI. Deliberately ungated (confirmed with the "
        "project owner 2026-10-06): any authenticated caller, including other "
        "backends, may look up who holds what on any resource id — even one "
        "hidden from them in the catalog."
    ),
)
async def list_grants_for_resource(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    grant_repository: Annotated[PermissionGrantRepository, Depends(get_grant_repository)],
) -> list[GrantOut]:
    grants = await grant_repository.list_grants_for_resource(resource_id)
    return [_to_out(g) for g in grants]


@router.put(
    "/{resource_id}/{grantee_type}/{grantee_id}",
    response_model=GrantOut,
    summary="Grant (or change) a role for a user or team on a resource",
    description=(
        "`grantee_type` is `user` or `team`. Requires the caller's effective_role at "
        "the resource be Manager (Editor/Viewer only) or Admin (any role); for a "
        "`user` grantee, the caller must also be transitively above them in the org "
        "chart, unless the resource sits inside the caller's own personal workspace. "
        "A re-grant of the exact same role is a no-op and logs nothing to the audit "
        "trail."
    ),
)
async def set_grant(
    resource_id: str,
    grantee_type: GranteeTypePath,
    grantee_id: str,
    body: SetGrantRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    permission_grant_service: Annotated[
        PermissionGrantService, Depends(get_permission_grant_service)
    ],
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
) -> GrantOut:
    await _ensure_resource_exists(resource_id, resource_repository)
    grantee = _to_grantee(grantee_type, grantee_id)
    grant = await permission_grant_service.grant(current_user, grantee, resource_id, body.role)
    return _to_out(grant)


@router.delete(
    "/{resource_id}/{grantee_type}/{grantee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a user's or team's grant on a resource",
    description=(
        "Same authorization as PUT, EXCEPT an actor may always revoke their OWN "
        "user grant, regardless of role-rank or org-chart position — 'remove my own "
        "access' isn't delegation to anyone. This is what powers the frontend's "
        "'Remove access' action on Map/Layer nodes."
    ),
)
async def delete_grant(
    resource_id: str,
    grantee_type: GranteeTypePath,
    grantee_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    permission_grant_service: Annotated[
        PermissionGrantService, Depends(get_permission_grant_service)
    ],
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
) -> Response:
    await _ensure_resource_exists(resource_id, resource_repository)
    grantee = _to_grantee(grantee_type, grantee_id)
    await permission_grant_service.revoke(current_user, grantee, resource_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
