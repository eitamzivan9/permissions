from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from permissions_server.api.deps import (
    get_access_resolver,
    get_current_user,
    get_restriction_repository,
    get_restriction_service,
)
from permissions_server.api.routers.grants_router import GranteeTypePath, _to_grantee
from permissions_server.api.schemas.restriction_schemas import RestrictionOut, SetRestrictionRequest
from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.restriction_service import RestrictionService
from permissions_server.domain.entities import AuthenticatedUser, Restriction, Role
from permissions_server.domain.errors import ForbiddenError
from permissions_server.domain.ports.restriction_repository import RestrictionRepository

router = APIRouter(prefix="/restrictions", tags=["restrictions"])


def _to_out(restriction: Restriction) -> RestrictionOut:
    return RestrictionOut(
        grantee_type=restriction.grantee.grantee_type.value,
        user_id=restriction.grantee.user_id,
        team_id=restriction.grantee.team_id,
        resource_id=restriction.resource_id,
        role=restriction.role,
        granted_by=restriction.granted_by,
    )


@router.get("/{resource_id}", response_model=list[RestrictionOut])
async def list_restrictions(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    restriction_repository: Annotated[RestrictionRepository, Depends(get_restriction_repository)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
) -> list[RestrictionOut]:
    # Role.ADMIN alone is sufficient (no separate SUPER_EDITOR check needed):
    # effective_role already resolves SUPER_EDITOR to Role.ADMIN unconditionally.
    actor_role = await access_resolver.effective_role(resource_id, user_id=current_user.id)
    if actor_role is not Role.ADMIN:
        raise ForbiddenError(f"{current_user.id} may not view restrictions on {resource_id}")
    restrictions = await restriction_repository.list_restrictions_for_resource(resource_id)
    return [_to_out(r) for r in restrictions]


@router.put("/{resource_id}/{grantee_type}/{grantee_id}", response_model=RestrictionOut)
async def set_restriction(
    resource_id: str,
    grantee_type: GranteeTypePath,
    grantee_id: str,
    body: SetRestrictionRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    restriction_service: Annotated[RestrictionService, Depends(get_restriction_service)],
) -> RestrictionOut:
    grantee = _to_grantee(grantee_type, grantee_id)
    restriction = await restriction_service.set_restriction(
        current_user, grantee, resource_id, body.role
    )
    return _to_out(restriction)


@router.delete(
    "/{resource_id}/{grantee_type}/{grantee_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_restriction(
    resource_id: str,
    grantee_type: GranteeTypePath,
    grantee_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    restriction_service: Annotated[RestrictionService, Depends(get_restriction_service)],
) -> Response:
    grantee = _to_grantee(grantee_type, grantee_id)
    await restriction_service.revoke_restriction(current_user, grantee, resource_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
