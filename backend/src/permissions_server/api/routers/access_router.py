"""Access-transparency endpoints: explain or list who has what, and why."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from permissions_server.api.deps import get_access_transparency_service, get_current_user
from permissions_server.api.schemas.access_schemas import AccessSourceOut, GranteeInfoOut
from permissions_server.application.access_transparency_service import (
    AccessSource,
    AccessTransparencyService,
    GranteeInfo,
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


@router.get(
    "/my-access/{resource_id}",
    response_model=list[AccessSourceOut],
    summary="Explain the caller's own access to a resource",
    description=(
        "Every contributing source (a system role, or each grant at the nearest "
        "ancestor with any grant) for the CALLER's own effective_role at this "
        "resource, with is_effective marking the one that actually wins. Ungated — "
        "always allowed for the caller's own access."
    ),
)
async def my_access(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    access_transparency_service: Annotated[
        AccessTransparencyService, Depends(get_access_transparency_service)
    ],
) -> list[AccessSourceOut]:
    sources = await access_transparency_service.my_access(current_user, resource_id)
    return [_to_out(s) for s in sources]


@router.get(
    "/check-access/{resource_id}/{user_id}",
    response_model=list[AccessSourceOut],
    summary="Explain another user's access to a resource",
    description=(
        "Same breakdown as /my-access, but for `user_id` instead of the caller. "
        "Gated: the caller must hold Manager+ effective_role at the resource (or a "
        "system role) — a 403 otherwise."
    ),
)
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


def _grantee_info_to_out(info: GranteeInfo) -> GranteeInfoOut:
    return GranteeInfoOut(grantee_type=info.grantee_type.value, id=info.id, name=info.name)


@router.get(
    "/admins/{resource_id}",
    response_model=list[GranteeInfoOut],
    summary="List who holds Admin on a resource",
    description=(
        "Every grantee (user or team) that currently resolves to Admin at the nearest "
        "ancestor gating this resource (restriction-aware, same precedence "
        "AccessResolver.effective_role uses). Meant for 'who do I ask' when the "
        "caller's own effective_role here is None — ungated like /my-access, since it "
        "only makes sense to call on a resource already visible to the caller."
    ),
)
async def list_admins(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    access_transparency_service: Annotated[
        AccessTransparencyService, Depends(get_access_transparency_service)
    ],
) -> list[GranteeInfoOut]:
    infos = await access_transparency_service.list_admins(resource_id)
    return [_grantee_info_to_out(i) for i in infos]
