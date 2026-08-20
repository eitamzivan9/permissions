"""Create, move, and delete Workspace/Folder/Map/Group/Layer resources."""

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


@router.get(
    "/my-workspace",
    response_model=ResourceOut,
    summary="Get or create the caller's personal Workspace",
    description=(
        "Idempotent: every authenticated user gets exactly one personal root "
        "Workspace, identified by owner_id. Creates it (self-admin by construction) "
        "on first call, returns the existing one on every call after."
    ),
)
async def get_my_workspace(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.get_or_create_my_workspace(current_user)
    return _to_out(resource)


@router.post(
    "/workspaces",
    response_model=ResourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team (non-personal) root Workspace",
    description=(
        "SUPER_EDITOR-only (403 otherwise). Creates a new root Workspace with no "
        "owner_id and grants Admin to `admin_user_id`, which need not be the caller."
    ),
)
async def create_team_workspace(
    body: CreateTeamWorkspaceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.create_team_workspace(
        current_user, name=body.name, admin_user_id=body.admin_user_id
    )
    return _to_out(resource)


@router.post(
    "",
    response_model=ResourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a child resource under a parent",
    description=(
        "Requires the caller hold Editor+ effective_role at `parent_id`. The caller "
        "is auto-granted Admin on the new resource. Accepts any resource type "
        "(Workspace/Folder/Map/Group/Layer) with no backend restriction — the "
        "frontend only offers Folder (this server doesn't own Map/Layer/Group data; "
        "creating those is meant to happen server-to-server, or manually until that "
        "integration exists)."
    ),
)
async def create_resource(
    body: CreateResourceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.create_child(
        current_user, type=body.type, name=body.name, parent_id=body.parent_id
    )
    return _to_out(resource)


@router.patch(
    "/{resource_id}/move",
    response_model=ResourceOut,
    summary="Move a resource to a new parent",
    description=(
        "Requires Admin at `resource_id` (the resource being moved) and Editor+ at "
        "`new_parent_id` (the destination). Rejects moving a resource into its own "
        "subtree. The frontend triggers this via drag-and-drop, but the endpoint "
        "itself is drag-and-drop-agnostic — any caller with the right roles may call "
        "it directly."
    ),
)
async def move_resource(
    resource_id: str,
    body: MoveResourceRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceOut:
    resource = await resource_service.move(current_user, resource_id, body.new_parent_id)
    return _to_out(resource)


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resource",
    description=(
        "Admin-only. For Workspace/Folder/Group, only succeeds when the resource has "
        "no children (409 otherwise) — this server never bulk-wipes Map/Layer data "
        "nested under a folder-level delete. Map/Layer keep the original "
        "unconditional-cascade behavior: every grant and restriction anywhere in the "
        "subtree is cleaned up first, then the resource rows themselves."
    ),
)
async def delete_resource(
    resource_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    resource_service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Response:
    await resource_service.delete(current_user, resource_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
