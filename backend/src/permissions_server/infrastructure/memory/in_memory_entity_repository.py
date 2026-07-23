"""Generic in-memory implementation of EntityRepository, shared by the
Resource and Team repositories so the get/list/search logic exists exactly
once."""

from __future__ import annotations

from typing import Generic, Iterable, Protocol, TypeVar

from permissions_server.domain.ports.entity_repository import Page


class _HasIdAndName(Protocol):
    id: str
    name: str


T = TypeVar("T", bound=_HasIdAndName)


class InMemoryEntityRepository(Generic[T]):
    def __init__(self, items: Iterable[T]) -> None:
        self._by_id: dict[str, T] = {item.id: item for item in items}

    async def get_by_id(self, entity_id: str) -> T | None:
        return self._by_id.get(entity_id)

    async def list_page(
        self, *, search: str | None, page: int, page_size: int
    ) -> Page[T]:
        items = list(self._by_id.values())
        if search:
            query = search.lower()
            items = [item for item in items if query in item.name.lower()]
        items.sort(key=lambda item: item.name)

        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]
        return Page(items=page_items, total=total, page=page, page_size=page_size)
