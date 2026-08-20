"""In-memory ResourceRepository — Phase 1 storage, used when PERMISSIONS_DATABASE_URL is unset."""

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
        self, resource_type: ResourceType, *, page: int, page_size: int, pinned_id: str | None = None
    ) -> Page[Resource]:
        items = [r for r in self._by_id.values() if r.type is resource_type]
        items.sort(key=lambda r: (r.id != pinned_id, r.name))

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
        owner_id: str | None = None,
    ) -> Resource:
        resource = Resource(
            id=uuid4().hex,
            type=type,
            name=name,
            parent_id=parent_id,
            inherits_from_parent=inherits_from_parent,
            owner_id=owner_id,
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
            owner_id=current.owner_id,
        )
        self._by_id[resource_id] = updated
        return updated

    async def find_workspace_by_owner(self, owner_id: str) -> Resource | None:
        return next(
            (
                r
                for r in self._by_id.values()
                if r.type is ResourceType.WORKSPACE and r.owner_id == owner_id
            ),
            None,
        )

    async def move(self, resource_id: str, new_parent_id: str) -> Resource:
        current = self._by_id[resource_id]
        updated = Resource(
            id=current.id,
            type=current.type,
            name=current.name,
            parent_id=new_parent_id,
            inherits_from_parent=current.inherits_from_parent,
            owner_id=current.owner_id,
        )
        self._by_id[resource_id] = updated
        return updated

    async def descendant_ids(self, resource_id: str) -> list[str]:
        ids = [resource_id]
        frontier = [resource_id]
        while frontier:
            children = [r.id for r in self._by_id.values() if r.parent_id in frontier]
            ids.extend(children)
            frontier = children
        return ids

    async def delete(self, resource_id: str) -> None:
        for descendant_id in await self.descendant_ids(resource_id):
            self._by_id.pop(descendant_id, None)
