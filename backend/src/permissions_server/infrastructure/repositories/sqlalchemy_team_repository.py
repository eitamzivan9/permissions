"""PostgreSQL-backed TeamRepository, used when PERMISSIONS_DATABASE_URL is set."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import Team
from permissions_server.domain.ports.entity_repository import Page
from permissions_server.infrastructure.db.models import TeamMembershipModel, TeamModel
from permissions_server.infrastructure.repositories._pagination import paginate


def _to_domain(model: TeamModel) -> Team:
    return Team(id=model.id, name=model.name)


class SqlAlchemyTeamRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_by_id(self, entity_id: str) -> Team | None:
        async with self._sessionmaker() as session:
            model = await session.get(TeamModel, entity_id)
            return _to_domain(model) if model else None

    async def list_page(self, *, search: str | None, page: int, page_size: int) -> Page[Team]:
        async with self._sessionmaker() as session:
            stmt = select(TeamModel)
            if search:
                stmt = stmt.where(TeamModel.name.ilike(f"%{search}%"))
            stmt = stmt.order_by(TeamModel.name)
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return Page(
                items=[_to_domain(r) for r in rows], total=total, page=page, page_size=page_size
            )

    async def list_members(self, team_id: str) -> list[str]:
        async with self._sessionmaker() as session:
            stmt = (
                select(TeamMembershipModel.user_id)
                .where(TeamMembershipModel.team_id == team_id)
                .order_by(TeamMembershipModel.user_id)
            )
            return list((await session.execute(stmt)).scalars().all())

    async def list_teams_for_user(self, user_id: str) -> list[Team]:
        async with self._sessionmaker() as session:
            stmt = (
                select(TeamModel)
                .join(TeamMembershipModel, TeamMembershipModel.team_id == TeamModel.id)
                .where(TeamMembershipModel.user_id == user_id)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def add_member(self, team_id: str, user_id: str) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(TeamMembershipModel, (team_id, user_id))
            if existing is None:
                session.add(TeamMembershipModel(team_id=team_id, user_id=user_id))
                await session.commit()

    async def remove_member(self, team_id: str, user_id: str) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(TeamMembershipModel, (team_id, user_id))
            if existing is not None:
                await session.delete(existing)
                await session.commit()

    async def create(self, name: str) -> Team:
        async with self._sessionmaker() as session:
            model = TeamModel(id=uuid4().hex, name=name)
            session.add(model)
            await session.commit()
            return _to_domain(model)
