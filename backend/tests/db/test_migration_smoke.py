"""The literal thing backend/pyproject.toml's coverage `omit` comment always
claimed existed: a migration smoke test that runs `alembic upgrade head`
against a real Postgres and checks the resulting schema."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.db.conftest import run_alembic_upgrade_head

_EXPECTED_TABLES = {
    "resources",
    "teams",
    "team_memberships",
    "permission_grants",
    "restrictions",
    "system_roles",
    "audit_log",
    "alembic_version",
}


async def test_ltree_extension_installed(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with sessionmaker() as session:
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'ltree'")
        )
        assert result.scalar_one_or_none() == "ltree"


async def test_all_tables_created(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    async with sessionmaker() as session:
        result = await session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        assert {row[0] for row in result} == _EXPECTED_TABLES


def test_alembic_upgrade_head_is_idempotent(migrated_database_url: str) -> None:
    # migrated_database_url already ran this once (session-scoped fixture);
    # running it again against the same, now-current database must be a no-op,
    # not an error — this is exactly what docker-entrypoint.sh relies on by
    # running it unconditionally on every container start.
    run_alembic_upgrade_head(migrated_database_url)
