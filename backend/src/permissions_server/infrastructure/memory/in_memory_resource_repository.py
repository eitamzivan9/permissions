from __future__ import annotations

from uuid import uuid4

from permissions_server.domain.entities import Resource, ResourceType
from permissions_server.domain.ports.entity_repository import Page
from permissions_server.infrastructure.memory.in_memory_entity_repository import (
    InMemoryEntityRepository,
)
from permissions_server.infrastructure.seed_data import RESOURCES


class InMemoryResourceRepository(InMemoryEntityRepository[Resource]):
    def __init__(self) -> None:
        super().__init__(RESOURCES)

    async def children_of(self, resource_id: str) -> list[Resource]:
        children = [r for r in self._by_id.values() if r.parent_id == resource_id]
        children.sort(key=lambda r: r.name)
        return children

    async def path_to_root(self, resource_id: str) -> list[Resource]:
        chain: list[Resource] = []
        visited: set[str] = set()
        current = self._by_id.get(resource_id)
        while current is not None:
            if current.id in visited:
                break  # cycle guard, same style as mock_org_hierarchy
            visited.add(current.id)
            chain.append(current)
            current = self._by_id.get(current.parent_id) if current.parent_id else None
        return list(reversed(chain))

    async def list_by_type(
        self, resource_type: ResourceType, *, page: int, page_size: int
    ) -> Page[Resource]:
        items = [r for r in self._by_id.values() if r.type is resource_type]
        items.sort(key=lambda r: r.name)

        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]
        return Page(items=page_items, total=total, page=page, page_size=page_size)

    async def create(
        self,
        *,
        type: ResourceType,
        name: str,
        parent_id: str | None,
        inherits_from_parent: bool = True,
    ) -> Resource:
        resource = Resource(
            id=uuid4().hex,
            type=type,
            name=name,
            parent_id=parent_id,
            inherits_from_parent=inherits_from_parent,
        )
        self._by_id[resource.id] = resource
        return resource

    async def set_inherits_from_parent(self, resource_id: str, value: bool) -> Resource:
        current = self._by_id[resource_id]
        updated = Resource(
            id=current.id,
            type=current.type,
            name=current.name,
            parent_id=current.parent_id,
            inherits_from_parent=value,
        )
        self._by_id[resource_id] = updated
        return updated
