"""Covers main.py's lifespan() DB-mode branch, which the rest of the suite
never exercises (tests/conftest.py force-unsets PERMISSIONS_DATABASE_URL so
every other test runs against in-memory repos). asyncpg's engine/session
construction is lazy — no real connection attempt happens until a query
actually runs — so this can verify the wiring itself without a live
Postgres, matching the same hermetic-suite boundary documented in
pyproject.toml's [tool.coverage.run] omit list for the SQLAlchemy repository
files themselves."""

from fastapi import FastAPI

import permissions_server.main as main_module
from permissions_server.config import Settings
from permissions_server.infrastructure.repositories.sqlalchemy_resource_repository import (
    SqlAlchemyResourceRepository,
)


async def test_lifespan_wires_sqlalchemy_repositories_when_database_url_set(monkeypatch):
    fake_settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/does-not-need-to-exist"
    )
    monkeypatch.setattr(main_module, "get_settings", lambda: fake_settings)

    app = FastAPI()
    async with main_module.lifespan(app):
        assert isinstance(app.state.resource_repository, SqlAlchemyResourceRepository)
        assert app.state.user_directory is not None
    # __aexit__ ran engine.dispose() with zero connections ever opened — the
    # absence of an exception here is the assertion.
