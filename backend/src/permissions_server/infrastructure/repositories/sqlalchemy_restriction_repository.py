from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import Grantee, Restriction, Role
from permissions_server.infrastructure.db.models import RestrictionModel
from permissions_server.infrastructure.repositories.sqlalchemy_grant_repository import (
    grantee_key,
)


def _to_domain(model: RestrictionModel) -> Restriction:
    grantee = Grantee(model.grantee_type, user_id=model.user_id, team_id=model.team_id)
    return Restriction(
        grantee=grantee, resource_id=model.resource_id, role=model.role, granted_by=model.granted_by
    )


class SqlAlchemyRestrictionRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_restriction(self, grantee: Grantee, resource_id: str) -> Restriction | None:
        async with self._sessionmaker() as session:
            model = await self._find(session, grantee, resource_id)
            return _to_domain(model) if model else None

    async def list_restrictions_for_resource(self, resource_id: str) -> list[Restriction]:
        async with self._sessionmaker() as session:
            stmt = select(RestrictionModel).where(RestrictionModel.resource_id == resource_id)
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def list_restrictions_for_resource_ids(
        self, resource_ids: list[str]
    ) -> list[Restriction]:
        if not resource_ids:
            return []
        async with self._sessionmaker() as session:
            stmt = select(RestrictionModel).where(
                RestrictionModel.resource_id.in_(resource_ids)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def list_restrictions_for_grantees(self, grantees: list[Grantee]) -> list[Restriction]:
        if not grantees:
            return []
        keys = [grantee_key(g) for g in grantees]
        async with self._sessionmaker() as session:
            stmt = select(RestrictionModel).where(RestrictionModel.grantee_key.in_(keys))
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def upsert_restriction(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> Restriction:
        async with self._sessionmaker() as session:
            existing = await self._find(session, grantee, resource_id)
            if existing is not None:
                existing.role = role
                existing.granted_by = granted_by
                await session.commit()
                return _to_domain(existing)

            model = RestrictionModel(
                id=uuid4().hex,
                grantee_type=grantee.grantee_type,
                user_id=grantee.user_id,
                team_id=grantee.team_id,
                resource_id=resource_id,
                role=role,
                granted_by=granted_by,
                grantee_key=grantee_key(grantee),
            )
            session.add(model)
            await session.commit()
            return _to_domain(model)

    async def delete_restriction(self, grantee: Grantee, resource_id: str) -> None:
        async with self._sessionmaker() as session:
            existing = await self._find(session, grantee, resource_id)
            if existing is not None:
                await session.delete(existing)
                await session.commit()

    async def delete_restrictions_for_resource_ids(self, resource_ids: list[str]) -> None:
        if not resource_ids:
            return
        async with self._sessionmaker() as session:
            stmt = delete(RestrictionModel).where(RestrictionModel.resource_id.in_(resource_ids))
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def _find(
        session: AsyncSession, grantee: Grantee, resource_id: str
    ) -> RestrictionModel | None:
        stmt = select(RestrictionModel).where(
            RestrictionModel.grantee_key == grantee_key(grantee),
            RestrictionModel.resource_id == resource_id,
        )
        return (await session.execute(stmt)).scalar_one_or_none()
