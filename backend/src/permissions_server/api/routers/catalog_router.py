from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from permissions_server.api.deps import get_catalog_service, get_current_user
from permissions_server.api.schemas.catalog_schemas import CatalogItemOut, CatalogPageOut
from permissions_server.application.catalog_service import CatalogItem, CatalogService
from permissions_server.domain.entities import AuthenticatedUser

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _to_out(item: CatalogItem) -> CatalogItemOut:
    return CatalogItemOut(
        id=item.id,
        type=item.type,
        name=item.name,
        effective_role=item.effective_role,
        can_manage=item.can_manage,
        can_fetch=item.can_fetch,
        children=[_to_out(child) for child in item.children],
    )


@router.get("", response_model=CatalogPageOut)
async def get_catalog(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CatalogPageOut:
    result = await catalog_service.get_catalog(
        current_user.id, search=q, page=page, page_size=page_size
    )
    return CatalogPageOut(
        items=[_to_out(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )
