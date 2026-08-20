"""PostgreSQL-backed AuditLogRepository, used when PERMISSIONS_DATABASE_URL is set."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import AuditLogEntry, Grantee
from permissions_server.domain.ports.entity_repository import Page
from permissions_server.infrastructure.db.models import AuditLogModel
from permissions_server.infrastructure.repositories._pagination import paginate


def _to_domain(model: AuditLogModel) -> AuditLogEntry:
    grantee = Grantee(model.grantee_type, user_id=model.user_id, team_id=model.team_id)
    return AuditLogEntry(
        id=model.id,
        actor_id=model.actor_id,
        grantee=grantee,
        resource_id=model.resource_id,
        role=model.role,
        action=model.action,
        timestamp=model.timestamp,
    )


class SqlAlchemyAuditLogRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def append(self, entry: AuditLogEntry) -> None:
        async with self._sessionmaker() as session:
            model = AuditLogModel(
                id=entry.id,
                actor_id=entry.actor_id,
                grantee_type=entry.grantee.grantee_type,
                user_id=entry.grantee.user_id,
                team_id=entry.grantee.team_id,
                resource_id=entry.resource_id,
                role=entry.role,
                action=entry.action,
                timestamp=entry.timestamp,
            )
            session.add(model)
            await session.commit()

    async def list_for_resource(
        self, resource_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        async with self._sessionmaker() as session:
            stmt = (
                select(AuditLogModel)
                .where(AuditLogModel.resource_id == resource_id)
                .order_by(AuditLogModel.timestamp.desc())
            )
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return Page(
                items=[_to_domain(r) for r in rows], total=total, page=page, page_size=page_size
            )

    async def list_for_actor(
        self, actor_id: str, *, page: int, page_size: int
    ) -> Page[AuditLogEntry]:
        async with self._sessionmaker() as session:
            stmt = (
                select(AuditLogModel)
                .where(AuditLogModel.actor_id == actor_id)
                .order_by(AuditLogModel.timestamp.desc())
            )
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return Page(
                items=[_to_domain(r) for r in rows], total=total, page=page, page_size=page_size
            )
