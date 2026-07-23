from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import Resource, ResourceType
from permissions_server.domain.ports.entity_repository import EntityRepository, Page


class ResourceRepository(EntityRepository[Resource], Protocol):
    async def children_of(self, resource_id: str) -> list[Resource]:
        """Direct children only, one level down."""
        ...

    async def path_to_root(self, resource_id: str) -> list[Resource]:
        """[root, ..., resource itself] — root-first, inclusive. Single-element
        list for a Workspace. This is the hook a Phase-2 ltree adapter turns
        into one indexed query; kept list-returning so Phase 1's O(depth) walk
        is a drop-in swap later, not a shape change."""
        ...

    async def list_by_type(
        self, resource_type: ResourceType, *, page: int, page_size: int
    ) -> Page[Resource]:
        """All resources of one type (e.g. every Workspace, or every Map),
        for the catalog's top-level pagination and /external/v1/my-access."""
        ...

    async def create(
        self,
        *,
        type: ResourceType,
        name: str,
        parent_id: str | None,
        inherits_from_parent: bool = True,
    ) -> Resource:
        """Persists a new node. Parent/child type legality (is_valid_child) is
        the CALLER's job, not this repo's — the repo only knows how to store
        a row."""
        ...

    async def set_inherits_from_parent(self, resource_id: str, value: bool) -> Resource:
        """Flip the inheritance-barrier flag on an existing resource (see
        Resource.inherits_from_parent) without touching any grant."""
        ...
