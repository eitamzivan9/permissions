from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from permissions_server.api.deps import get_access_transparency_service, get_current_user
from permissions_server.api.schemas.access_schemas import AccessSourceOut
from permissions_server.application.access_transparency_service import (
    AccessSource,
    AccessTransparencyService,
)
from permissions_server.domain.entities import AuthenticatedUser

router = APIRouter(prefix="/access", tags=["access"])


def _to_out(source: AccessSource) -> AccessSourceOut:
    grantee = source.grantee
    return AccessSourceOut(
        grantee_type=grantee.grantee_type.value if grantee else None,
        user_id=grantee.user_id if grantee else None,
        team_id=grantee.team_id if grantee else None,
        system_role=source.system_role,
        origin_resource_id=source.origin_resource_id,
        role=source.role,
        is_effective=source.is_effective,
    )


@router.get("/my-access/{resource_id}", response_model=list[AccessSourceOut])
async def my_access(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    access_transparency_service: Annotated[
        AccessTransparencyService, Depends(get_access_transparency_service)
    ],
) -> list[AccessSourceOut]:
    sources = await access_transparency_service.my_access(current_user, resource_id)
    return [_to_out(s) for s in sources]


@router.get("/check-access/{resource_id}/{user_id}", response_model=list[AccessSourceOut])
async def check_access(
    resource_id: str,
    user_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    access_transparency_service: Annotated[
        AccessTransparencyService, Depends(get_access_transparency_service)
    ],
) -> list[AccessSourceOut]:
    sources = await access_transparency_service.check_access(current_user, user_id, resource_id)
    return [_to_out(s) for s in sources]
