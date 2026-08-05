from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from permissions_server.api.deps import get_current_user, get_resource_service
from permissions_server.api.schemas.resource_schemas import (
    CreateResourceRequest,
    CreateTeamWorkspaceRequest,
    MoveResourceRequest,
    ResourceOut,
)
from permissions_server.application.resource_service import ResourceService
from permissions_server.domain.entities import AuthenticatedUser, Resource

router = APIRouter(prefix="/resources", tags=["resources"])


def _to_out(resource: Resource) -> ResourceOut:
    return ResourceOut(
        id=resource.id,
        type=resource.type,
        name=resource.name,
        parent_id=resource.parent_id,
        inherits_from_parent=resource.inherits_from_parent,
        owner_id=resource.owner_id,
    )


@router.get("/my-workspace", response_model=ResourceOut)
async def get_my_workspace(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.get_or_create_my_workspace(current_user)
    return _to_out(resource)


@router.post("/workspaces", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_team_workspace(
    body: CreateTeamWorkspaceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.create_team_workspace(
        current_user, name=body.name, admin_user_id=body.admin_user_id
    )
    return _to_out(resource)


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    body: CreateResourceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.create_child(
        current_user, type=body.type, name=body.name, parent_id=body.parent_id
    )
    return _to_out(resource)


@router.patch("/{resource_id}/move", response_model=ResourceOut)
async def move_resource(
    resource_id: str,
    body: MoveResourceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.move(current_user, resource_id, body.new_parent_id)
    return _to_out(resource)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Response:
    await resource_service.delete(current_user, resource_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
