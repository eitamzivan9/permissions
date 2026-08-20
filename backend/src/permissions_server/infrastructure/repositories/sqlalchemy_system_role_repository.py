"""PostgreSQL-backed SystemRoleRepository, used when PERMISSIONS_DATABASE_URL is set."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import SystemRole
from permissions_server.infrastructure.db.models import SystemRoleModel


class SqlAlchemySystemRoleRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def list_system_roles(self, user_id: str) -> frozenset[SystemRole]:
        async with self._sessionmaker() as session:
            stmt = select(SystemRoleModel.role).where(SystemRoleModel.user_id == user_id)
            roles = (await session.execute(stmt)).scalars().all()
            return frozenset(roles)

    async def grant_system_role(self, user_id: str, role: SystemRole, granted_by: str) -> None:
        # granted_by is intentionally not persisted — the in-memory
        # implementation this mirrors doesn't track it either (see
        # InMemorySystemRoleRepository.grant_system_role), and both
        # implementations must behave identically (LSP).
        async with self._sessionmaker() as session:
            existing = await session.get(SystemRoleModel, (user_id, role))
            if existing is None:
                session.add(SystemRoleModel(user_id=user_id, role=role))
                await session.commit()

    async def revoke_system_role(self, user_id: str, role: SystemRole) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(SystemRoleModel, (user_id, role))
            if existing is not None:
                await session.delete(existing)
                await session.commit()
