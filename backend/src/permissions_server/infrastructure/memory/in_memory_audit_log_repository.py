from __future__ import annotations

from permissions_server.domain.entities import AuditLogEntry
from permissions_server.domain.ports.entity_repository import Page


class InMemoryAuditLogRepository:
    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []

    async def append(self, entry: AuditLogEntry) -> None:
        self._entries.append(entry)

    async def list_for_resource(
        self, resource_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        matches = [e for e in self._entries if e.resource_id == resource_id]
        return self._paginate_newest_first(matches, page=page, page_size=page_size)

    async def list_for_actor(
        self, actor_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        matches = [e for e in self._entries if e.actor_id == actor_id]
        return self._paginate_newest_first(matches, page=page, page_size=page_size)

    @staticmethod
    def _paginate_newest_first(
        matches: list[AuditLogEntry], *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        matches = sorted(matches, key=lambda e: e.timestamp, reverse=True)
        total = len(matches)
        start = (page - 1) * page_size
        page_items = matches[start : start + page_size]
        return Page(items=page_items, total=total, page=page, page_size=page_size)
