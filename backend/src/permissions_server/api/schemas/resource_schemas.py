from __future__ import annotations

from pydantic import BaseModel

from permissions_server.domain.entities import ResourceType


class ResourceOut(BaseModel):
    id: str
    type: ResourceType
    name: str
    parent_id: str | None
    inherits_from_parent: bool
    owner_id: str | None


class CreateResourceRequest(BaseModel):
    type: ResourceType
    name: str
    parent_id: str


class CreateTeamWorkspaceRequest(BaseModel):
    name: str
    admin_user_id: str


class MoveResourceRequest(BaseModel):
    new_parent_id: str
