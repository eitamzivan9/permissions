"""PostgreSQL-backed PermissionGrantRepository, used when PERMISSIONS_DATABASE_URL is set."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import Grantee, PermissionGrant, Role
from permissions_server.infrastructure.db.models import PermissionGrantModel


def grantee_key(grantee: Grantee) -> str:
    """Always non-null and unique per (grantee_type, user_id, team_id) triple
    — see PermissionGrantModel.grantee_key for why a plain nullable composite
    unique constraint isn't enough. Public (no leading underscore) because
    scripts/seed.py also needs to compute it when inserting grants directly."""
    return f"{grantee.grantee_type.value}:{grantee.user_id or ''}:{grantee.team_id or ''}"


def _to_domain(model: PermissionGrantModel) -> PermissionGrant:
    grantee = Grantee(model.grantee_type, user_id=model.user_id, team_id=model.team_id)
    return PermissionGrant(
        grantee=grantee, resource_id=model.resource_id, role=model.role, granted_by=model.granted_by
    )


class SqlAlchemyGrantRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_grant(self, grantee: Grantee, resource_id: str) -> PermissionGrant | None:
        async with self._sessionmaker() as session:
            model = await self._find(session, grantee, resource_id)
            return _to_domain(model) if model else None

    async def list_grants_for_resource(self, resource_id: str) -> list[PermissionGrant]:
        async with self._sessionmaker() as session:
            stmt = select(PermissionGrantModel).where(
                PermissionGrantModel.resource_id == resource_id
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def list_grants_for_grantees(self, grantees: list[Grantee]) -> list[PermissionGrant]:
        if not grantees:
            return []
        keys = [grantee_key(g) for g in grantees]
        async with self._sessionmaker() as session:
            stmt = select(PermissionGrantModel).where(PermissionGrantModel.grantee_key.in_(keys))
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def upsert_grant(
        self, grantee: Grantee, resource_id: str, role: Role, granted_by: str
    ) -> PermissionGrant:
        async with self._sessionmaker() as session:
            existing = await self._find(session, grantee, resource_id)
            if existing is not None:
                existing.role = role
                existing.granted_by = granted_by
                await session.commit()
                return _to_domain(existing)

            model = PermissionGrantModel(
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

    async def delete_grant(self, grantee: Grantee, resource_id: str) -> None:
        async with self._sessionmaker() as session:
            existing = await self._find(session, grantee, resource_id)
            if existing is not None:
                await session.delete(existing)
                await session.commit()

    async def delete_grants_for_resource_ids(self, resource_ids: list[str]) -> None:
        if not resource_ids:
            return
        async with self._sessionmaker() as session:
            stmt = delete(PermissionGrantModel).where(
                PermissionGrantModel.resource_id.in_(resource_ids)
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def _find(
        session: AsyncSession, grantee: Grantee, resource_id: str
    ) -> PermissionGrantModel | None:
        stmt = select(PermissionGrantModel).where(
            PermissionGrantModel.grantee_key == grantee_key(grantee),
            PermissionGrantModel.resource_id == resource_id,
        )
        return (await session.execute(stmt)).scalar_one_or_none()
