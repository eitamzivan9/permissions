"""Shared read contract for entities identified by id and searchable by name.
Backs both ResourceRepository and TeamRepository instead of each defining its
own near-identical get/list/search methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class EntityRepository(Protocol[T]):
    async def get_by_id(self, entity_id: str) -> T | None: ...

    async def list_page(
        self, *, search: str | None, page: int, page_size: int
    ) -> Page[T]: ...
