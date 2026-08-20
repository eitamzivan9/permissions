"""Append-only audit trail port — no update/delete method by design."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import AuditLogEntry
from permissions_server.domain.ports.entity_repository import Page


class AuditLogRepository(Protocol):
    async def append(self, entry: AuditLogEntry) -> None: ...

    async def list_for_resource(
        self, resource_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        """Newest-first. Append-only — no update/delete method on this port,
        by design (an audit log you can edit isn't an audit log)."""
        ...

    async def list_for_actor(
        self, actor_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]: ...
