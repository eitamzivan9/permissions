"""FastAPI DI wiring. This is the ONLY module allowed to import concrete
infrastructure/ classes directly — everything else depends on domain.ports.

Repositories are built once at startup (see main.py's lifespan) and stored on
app.state; a per-request instance would silently reset all in-memory data on
every call. Application services are cheap, stateless wrappers around those
repos, so they're constructed fresh per request via normal FastAPI Depends
chaining — no need to cache them on app.state too."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.access_transparency_service import AccessTransparencyService
from permissions_server.application.audit_service import AuditService
from permissions_server.application.auth_service import AuthService
from permissions_server.application.catalog_service import CatalogService
from permissions_server.application.permission_grant_service import PermissionGrantService
from permissions_server.application.resource_service import ResourceService
from permissions_server.application.restriction_service import RestrictionService
from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.errors import UnauthorizedError
from permissions_server.domain.ports.audit_log_repository import AuditLogRepository
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.org_hierarchy import OrgHierarchy
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.restriction_repository import RestrictionRepository
from permissions_server.domain.ports.system_role_repository import SystemRoleRepository
from permissions_server.domain.ports.team_repository import TeamRepository
from permissions_server.domain.ports.token_issuer import TokenIssuer
from permissions_server.domain.ports.token_validator import TokenValidator
from permissions_server.domain.ports.user_directory import UserDirectory

_bearer_scheme = HTTPBearer(auto_error=False)


# --- repository providers: hand out the singletons app.state already holds ---


def get_resource_repository(request: Request) -> ResourceRepository:
    return request.app.state.resource_repository


def get_team_repository(request: Request) -> TeamRepository:
    return request.app.state.team_repository


def get_grant_repository(request: Request) -> PermissionGrantRepository:
    return request.app.state.grant_repository


def get_system_role_repository(request: Request) -> SystemRoleRepository:
    return request.app.state.system_role_repository


def get_audit_log_repository(request: Request) -> AuditLogRepository:
    return request.app.state.audit_log_repository


def get_restriction_repository(request: Request) -> RestrictionRepository:
    return request.app.state.restriction_repository


def get_user_directory(request: Request) -> UserDirectory:
    return request.app.state.user_directory


def get_org_hierarchy(request: Request) -> OrgHierarchy:
    return request.app.state.org_hierarchy


def get_token_issuer(request: Request) -> TokenIssuer:
    return request.app.state.token_issuer


def get_token_validator(request: Request) -> TokenValidator:
    return request.app.state.token_validator


# --- application service providers ---


def get_access_resolver(
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
    grant_repository: Annotated[PermissionGrantRepository, Depends(get_grant_repository)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
    system_role_repository: Annotated[SystemRoleRepository, Depends(get_system_role_repository)],
    restriction_repository: Annotated[RestrictionRepository, Depends(get_restriction_repository)],
) -> AccessResolver:
    return AccessResolver(
        resource_repository,
        grant_repository,
        team_repository,
        system_role_repository,
        restriction_repository,
    )


def get_catalog_service(
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
) -> CatalogService:
    return CatalogService(resource_repository, access_resolver)


def get_audit_service(
    audit_log_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_log_repository)


def get_permission_grant_service(
    grant_repository: Annotated[PermissionGrantRepository, Depends(get_grant_repository)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    org_hierarchy: Annotated[OrgHierarchy, Depends(get_org_hierarchy)],
    user_directory: Annotated[UserDirectory, Depends(get_user_directory)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
) -> PermissionGrantService:
    return PermissionGrantService(
        grant_repository,
        access_resolver,
        org_hierarchy,
        user_directory,
        audit_service,
        resource_repository,
    )


def get_access_transparency_service(
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    user_directory: Annotated[UserDirectory, Depends(get_user_directory)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> AccessTransparencyService:
    return AccessTransparencyService(access_resolver, user_directory, team_repository)


def get_auth_service(
    user_directory: Annotated[UserDirectory, Depends(get_user_directory)],
    token_issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
) -> AuthService:
    return AuthService(user_directory, token_issuer)


def get_resource_service(
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    permission_grant_service: Annotated[
        PermissionGrantService, Depends(get_permission_grant_service)
    ],
    grant_repository: Annotated[PermissionGrantRepository, Depends(get_grant_repository)],
    restriction_repository: Annotated[RestrictionRepository, Depends(get_restriction_repository)],
) -> ResourceService:
    return ResourceService(
        resource_repository,
        access_resolver,
        permission_grant_service,
        grant_repository,
        restriction_repository,
    )


def get_restriction_service(
    restriction_repository: Annotated[RestrictionRepository, Depends(get_restriction_repository)],
    access_resolver: Annotated[AccessResolver, Depends(get_access_resolver)],
    org_hierarchy: Annotated[OrgHierarchy, Depends(get_org_hierarchy)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    resource_repository: Annotated[ResourceRepository, Depends(get_resource_repository)],
) -> RestrictionService:
    return RestrictionService(
        restriction_repository, access_resolver, org_hierarchy, audit_service, resource_repository
    )


# --- current-user dependency: every Bearer-auth route depends on this ---


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    token_validator: Annotated[TokenValidator, Depends(get_token_validator)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )
    try:
        return await token_validator.validate(credentials.credentials)
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
