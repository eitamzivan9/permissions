"""DB-backed test tier — the counterpart to tests/unit (in-memory) and
tests/integration (HTTP-over-in-memory). Exercises exactly what
pyproject.toml's coverage `omit` list excludes from the hermetic suite: the
SQLAlchemy repositories, infrastructure/db/session.py, infrastructure/db/
types.py (the ltree TypeDecorator), and infrastructure/repositories/
_pagination.py — none of which can execute meaningfully without a real
Postgres connection.

Deliberately keyed off PERMISSIONS_TEST_DATABASE_URL, not
PERMISSIONS_DATABASE_URL — tests/conftest.py force-unsets the latter so the
rest of the suite stays hermetic, and this tier must not fight that. Skipped
entirely (not failed) when the variable isn't set, so a plain `pytest` run on
a machine without Postgres still passes; see DATABASE.md's "DB-backed test
tier" section for how to point it at a real instance.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.infrastructure.db.session import build_engine_and_sessionmaker
from permissions_server.infrastructure.repositories.sqlalchemy_audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from permissions_server.infrastructure.repositories.sqlalchemy_grant_repository import (
    SqlAlchemyGrantRepository,
)
from permissions_server.infrastructure.repositories.sqlalchemy_resource_repository import (
    SqlAlchemyResourceRepository,
)
from permissions_server.infrastructure.repositories.sqlalchemy_restriction_repository import (
    SqlAlchemyRestrictionRepository,
)
from permissions_server.infrastructure.repositories.sqlalchemy_system_role_repository import (
    SqlAlchemySystemRoleRepository,
)
from permissions_server.infrastructure.repositories.sqlalchemy_team_repository import (
    SqlAlchemyTeamRepository,
)

pytestmark = pytest.mark.db

_BACKEND_DIR = Path(__file__).resolve().parents[2]

# Every app table (not alembic_version) — truncated before each test so tests
# stay isolated without a savepoint-per-test scheme. A shared outer
# transaction wouldn't actually work here: each repository method opens and
# commits its own session (see e.g. SqlAlchemyResourceRepository), so nothing
# would be left uncommitted for an outer rollback to undo.
_TABLES = (
    "resources",
    "teams",
    "team_memberships",
    "permission_grants",
    "restrictions",
    "system_roles",
    "audit_log",
)


def _require_database_url() -> str:
    url = os.environ.get("PERMISSIONS_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "PERMISSIONS_TEST_DATABASE_URL not set — skipping DB-backed tests "
            "(see DATABASE.md's 'DB-backed test tier' section)"
        )
    return url


def run_alembic_upgrade_head(database_url: str) -> None:
    """Runs the exact command docker-entrypoint.sh / DATABASE.md's manual setup
    both use, as a subprocess against database_url — never alembic's Python API
    in-process, since that would share this process's already-`lru_cache`d
    `get_settings()` with the rest of the test session. Retries briefly: a
    freshly-started CI Postgres service container can take a moment to accept
    connections."""
    import time

    env = {**os.environ, "PERMISSIONS_DATABASE_URL": database_url}
    last_result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(10):
        last_result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=_BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        if last_result.returncode == 0:
            return
        time.sleep(1 if attempt < 5 else 2)
    raise RuntimeError(
        f"alembic upgrade head failed after retries:\n{last_result.stderr}"
    )


@pytest.fixture(scope="session")
def migrated_database_url() -> str:
    url = _require_database_url()
    run_alembic_upgrade_head(url)
    return url


@pytest_asyncio.fixture
async def sessionmaker(
    migrated_database_url: str,
) -> async_sessionmaker[AsyncSession]:
    """Function-scoped, deliberately not session-scoped: an async engine's
    connection pool is bound to the event loop it was created on, and
    pytest-asyncio gives each test function its own event loop. A
    session-scoped engine would work for exactly one test and then fail every
    test after it with asyncpg 'another operation is in progress' errors —
    building a fresh engine per test (cheap; nothing else in this tier holds
    a connection open across tests) is what keeps this actually working."""
    engine, sm = build_engine_and_sessionmaker(migrated_database_url)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} CASCADE"))
    yield sm
    await engine.dispose()


@pytest.fixture
def resource_repo(sessionmaker: async_sessionmaker[AsyncSession]) -> SqlAlchemyResourceRepository:
    return SqlAlchemyResourceRepository(sessionmaker)


@pytest.fixture
def team_repo(sessionmaker: async_sessionmaker[AsyncSession]) -> SqlAlchemyTeamRepository:
    return SqlAlchemyTeamRepository(sessionmaker)


@pytest.fixture
def grant_repo(sessionmaker: async_sessionmaker[AsyncSession]) -> SqlAlchemyGrantRepository:
    return SqlAlchemyGrantRepository(sessionmaker)


@pytest.fixture
def restriction_repo(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> SqlAlchemyRestrictionRepository:
    return SqlAlchemyRestrictionRepository(sessionmaker)


@pytest.fixture
def system_role_repo(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> SqlAlchemySystemRoleRepository:
    return SqlAlchemySystemRoleRepository(sessionmaker)


@pytest.fixture
def audit_log_repo(sessionmaker: async_sessionmaker[AsyncSession]) -> SqlAlchemyAuditLogRepository:
    return SqlAlchemyAuditLogRepository(sessionmaker)
