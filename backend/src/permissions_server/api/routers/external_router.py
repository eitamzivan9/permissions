from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from permissions_server.api.deps import get_catalog_service, get_current_user
from permissions_server.application.catalog_service import CatalogService
from permissions_server.domain.entities import AuthenticatedUser, Role

router = APIRouter(prefix="/external/v1", tags=["external"])


class ExternalMapAccessOut(BaseModel):
    id: str
    name: str
    role: Role | None
    """None when the map has no direct/inherited role of its own but is still
    reachable via at least one accessible Layer inside it."""


class ExternalMyAccessPageOut(BaseModel):
    items: list[ExternalMapAccessOut]
    total: int
    page: int
    page_size: int


@router.get("/my-access", response_model=ExternalMyAccessPageOut)
async def get_my_access(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ExternalMyAccessPageOut:
    result = await catalog_service.get_external_access(
        current_user.id, page=page, page_size=page_size
    )
    return ExternalMyAccessPageOut(
        items=[
            ExternalMapAccessOut(id=item.id, name=item.name, role=item.role)
            for item in result.items
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )
