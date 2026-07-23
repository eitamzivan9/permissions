"""One-time (idempotent) loader: pushes seed_data.py's mock resource
tree/teams into Postgres, plus the same root-user bootstrap admin grant
main.py's in-memory lifespan creates automatically. Run after `alembic
upgrade head`:

    .venv\\Scripts\\python.exe scripts\\seed.py

Inserts fixed ids straight into the ORM models rather than going through
ResourceRepository.create()/TeamRepository.create() — those always mint a
fresh uuid4 id, but seed_data.py's Resource rows reference each other by
fixed parent_id strings (e.g. "f-infrastructure" -> parent_id "ws-city"),
so the ids must be preserved exactly as written."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from permissions_server.config import get_settings
from permissions_server.domain.entities import Grantee, GranteeType, Role
from permissions_server.infrastructure.db.models import (
    PermissionGrantModel,
    ResourceModel,
    TeamMembershipModel,
    TeamModel,
)
from permissions_server.infrastructure.db.session import build_engine_and_sessionmaker
from permissions_server.infrastructure.db.types import sanitize_label
from permissions_server.infrastructure.repositories.sqlalchemy_grant_repository import grantee_key
from permissions_server.infrastructure.seed_data import RESOURCES, TEAM_MEMBERSHIPS, TEAMS

ROOT_USER_ID = "u001"  # same org-root convention as main.py's _seed_root_grants


async def seed() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("PERMISSIONS_DATABASE_URL is not set (backend/.env)")

    _engine, sessionmaker = build_engine_and_sessionmaker(settings.database_url)
    async with sessionmaker() as session:
        paths: dict[str, str] = {}
        for resource in RESOURCES:
            existing = await session.get(ResourceModel, resource.id)
            if existing is not None:
                paths[resource.id] = existing.path
                continue

            parent_path = paths.get(resource.parent_id) if resource.parent_id else None
            label = sanitize_label(resource.id)
            path = f"{parent_path}.{label}" if parent_path else label
            paths[resource.id] = path

            session.add(
                ResourceModel(
                    id=resource.id,
                    type=resource.type,
                    name=resource.name,
                    parent_id=resource.parent_id,
                    inherits_from_parent=resource.inherits_from_parent,
                    path=path,
                )
            )
        await session.commit()
        print(f"resources: {len(RESOURCES)} checked, paths computed for {len(paths)}")

        for team in TEAMS:
            if await session.get(TeamModel, team.id) is None:
                session.add(TeamModel(id=team.id, name=team.name))
        await session.commit()
        print(f"teams: {len(TEAMS)} checked")

        membership_count = 0
        for team_id, user_ids in TEAM_MEMBERSHIPS.items():
            for user_id in user_ids:
                if await session.get(TeamMembershipModel, (team_id, user_id)) is None:
                    session.add(TeamMembershipModel(team_id=team_id, user_id=user_id))
                    membership_count += 1
        await session.commit()
        print(f"team memberships: {membership_count} inserted")

        root_grantee = Grantee(GranteeType.USER, user_id=ROOT_USER_ID)
        key = grantee_key(root_grantee)
        grant_count = 0
        for resource in RESOURCES:
            if resource.parent_id is not None:
                continue
            stmt = select(PermissionGrantModel).where(
                PermissionGrantModel.grantee_key == key,
                PermissionGrantModel.resource_id == resource.id,
            )
            if (await session.execute(stmt)).scalar_one_or_none() is None:
                session.add(
                    PermissionGrantModel(
                        id=f"seed-root-{resource.id}",
                        grantee_type=GranteeType.USER,
                        user_id=ROOT_USER_ID,
                        team_id=None,
                        resource_id=resource.id,
                        role=Role.ADMIN,
                        granted_by="system-bootstrap",
                        grantee_key=key,
                    )
                )
                grant_count += 1
        await session.commit()
        print(f"root bootstrap grants: {grant_count} inserted")

    await _engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
