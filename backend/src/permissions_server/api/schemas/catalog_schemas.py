"""Wire schemas for api/routers/catalog_router.py."""

from __future__ import annotations

from pydantic import BaseModel

from permissions_server.domain.entities import ResourceType, Role


class CatalogItemOut(BaseModel):
    id: str
    type: ResourceType
    name: str
    effective_role: Role | None
    can_manage: bool
    can_fetch: bool
    children: list["CatalogItemOut"]


CatalogItemOut.model_rebuild()


class CatalogPageOut(BaseModel):
    items: list[CatalogItemOut]
    total: int
    page: int
    page_size: int
