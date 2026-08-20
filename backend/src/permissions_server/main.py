"""FastAPI app factory and startup wiring — builds either in-memory or SQLAlchemy repositories depending on PERMISSIONS_DATABASE_URL."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from permissions_server.api.error_handlers import register_error_handlers
from permissions_server.api.routers import (
    access_router,
    audit_router,
    auth_router,
    catalog_router,
    external_router,
    grants_router,
    resources_router,
    restrictions_router,
    teams_router,
)
from permissions_server.config import get_settings
from permissions_server.domain.entities import Grantee, GranteeType, Role
from permissions_server.infrastructure.auth.adfs_auth_mock_issuer import AdfsAuthMockTokenIssuer
from permissions_server.infrastructure.auth.adfs_auth_mock_validator import (
    AdfsAuthMockTokenValidator,
)
from permissions_server.infrastructure.auth.mock_org_hierarchy import MockOrgHierarchy
from permissions_server.infrastructure.auth.mock_user_directory import MockUserDirectory
from permissions_server.infrastructure.memory.in_memory_audit_log_repository import (
    InMemoryAuditLogRepository,
)
from permissions_server.infrastructure.memory.in_memory_grant_repository import InMemoryGrantRepository
from permissions_server.infrastructure.memory.in_memory_resource_repository import (
    InMemoryResourceRepository,
)
from permissions_server.infrastructure.memory.in_memory_restriction_repository import (
    InMemoryRestrictionRepository,
)
from permissions_server.infrastructure.memory.in_memory_system_role_repository import (
    InMemorySystemRoleRepository,
)
from permissions_server.infrastructure.memory.in_memory_team_repository import InMemoryTeamRepository
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
from permissions_server.infrastructure.seed_data import RESOURCES

# Mock-data-only bootstrap: with an empty grant table, nobody has Manager+ to
# delegate from, so nobody could ever make the first grant through the API.
# Seed the org root (the one user with no manager) with Admin on every
# top-level Workspace — Admin cascades the whole subtree via the
# nearest-ancestor climb, so one grant per Workspace replaces one grant per
# map. Phase 2 replaces this with whatever real grants already exist in
# Postgres — not a permanent rule, just a Phase 1 dev convenience.
ROOT_USER_ID = "u001"


async def _seed_root_grants(grant_repository: InMemoryGrantRepository) -> None:
    root_grantee = Grantee(GranteeType.USER, user_id=ROOT_USER_ID)
    for resource in RESOURCES:
        if resource.parent_id is None:
            await grant_repository.upsert_grant(
                root_grantee, resource.id, Role.ADMIN, granted_by="system-bootstrap"
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Built once here, not per-request — see api/deps.py docstring. Phase 2
    # swap point: branch on settings.database_url to build SQLAlchemy repos
    # instead, still stored the same way on app.state.
    settings = get_settings()
    if settings.database_url:
        engine, sessionmaker = build_engine_and_sessionmaker(settings.database_url)
        app.state.resource_repository = SqlAlchemyResourceRepository(sessionmaker)
        app.state.team_repository = SqlAlchemyTeamRepository(sessionmaker)
        app.state.grant_repository = SqlAlchemyGrantRepository(sessionmaker)
        app.state.system_role_repository = SqlAlchemySystemRoleRepository(sessionmaker)
        app.state.audit_log_repository = SqlAlchemyAuditLogRepository(sessionmaker)
        app.state.restriction_repository = SqlAlchemyRestrictionRepository(sessionmaker)
        # No _seed_root_grants() call: with real persistence, seeding is a
        # one-time step (scripts/seed.py), not something to redo on every
        # process start.
    else:
        app.state.resource_repository = InMemoryResourceRepository()
        app.state.team_repository = InMemoryTeamRepository()
        app.state.grant_repository = InMemoryGrantRepository()
        app.state.system_role_repository = InMemorySystemRoleRepository()
        app.state.audit_log_repository = InMemoryAuditLogRepository()
        app.state.restriction_repository = InMemoryRestrictionRepository()
        await _seed_root_grants(app.state.grant_repository)

    app.state.user_directory = MockUserDirectory()
    app.state.org_hierarchy = MockOrgHierarchy()
    app.state.token_issuer = AdfsAuthMockTokenIssuer()
    app.state.token_validator = AdfsAuthMockTokenValidator(app.state.user_directory)

    yield

    if settings.database_url:
        await engine.dispose()


OPENAPI_TAGS = [
    {"name": "auth", "description": "Login and identity — mocked ADFS today (see domain/ports/token_*)."},
    {"name": "catalog", "description": "The main resource-tree listing, annotated with the caller's own access."},
    {"name": "resources", "description": "Create, move, and delete Workspace/Folder/Map/Group/Layer resources."},
    {"name": "grants", "description": "Per-resource role grants for a user or team grantee."},
    {"name": "restrictions", "description": "The whitelist gate layered on top of ordinary grants."},
    {"name": "access", "description": "Access transparency: explain or list who has what, and why."},
    {"name": "audit", "description": "Append-only history of every grant/restriction change."},
    {"name": "teams", "description": "Team identity and membership (a Team is a grantee, not a user)."},
    {"name": "external", "description": "The one endpoint other internal apps call to check map access."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Permissions Server",
        description=(
            "Permissions/access-control server for the geography team's resource "
            "tree (workspaces, folders, maps, groups, layers). Owns permissions "
            "only — never resource feature data, never a users table."
        ),
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(auth_router.router)
    app.include_router(catalog_router.router)
    app.include_router(grants_router.router)
    app.include_router(external_router.router)
    app.include_router(teams_router.router)
    app.include_router(access_router.router)
    app.include_router(audit_router.router)
    app.include_router(resources_router.router)
    app.include_router(restrictions_router.router)

    return app


app = create_app()
