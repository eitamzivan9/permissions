"""Mock login and the caller's own identity/system-roles."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from permissions_server.api.deps import get_auth_service, get_current_user, get_system_role_repository
from permissions_server.api.schemas.auth_schemas import LoginRequest, LoginResponse, MeOut, MockUserOut
from permissions_server.application.auth_service import AuthService
from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.ports.system_role_repository import SystemRoleRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get(
    "/mock-users",
    response_model=list[MockUserOut],
    summary="List every mock user (dev/test login picker only)",
    description=(
        "Phase 1 only — lists the fixture-backed mock user directory so a dev login "
        "UI can offer a 'log in as' picker. Not authenticated itself, and will not "
        "exist once real ADFS login replaces the mock issuer."
    ),
)
async def list_mock_users(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> list[MockUserOut]:
    users = await auth_service.list_mock_users()
    return [MockUserOut(id=u.id, name=u.name, email=u.email) for u in users]


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in as a mock user (dev/test only)",
    description=(
        "Issues a mock bearer token for `user_id`, no password/credential check — "
        "this is the mocked stand-in for the real ADFS OIDC login flow, not yet "
        "wired in."
    ),
)
async def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    token = await auth_service.login(body.user_id)
    return LoginResponse(token=token)


@router.get(
    "/me",
    response_model=MeOut,
    summary="Get the caller's own identity and system-wide roles",
    description=(
        "Resolves the bearer token to identity plus any SUPER_EDITOR/SUPER_VIEWER "
        "system roles. The frontend calls this right after login, then fires "
        "GET /resources/my-workspace to ensure the caller's personal workspace exists."
    ),
)
async def get_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    system_role_repository: Annotated[SystemRoleRepository, Depends(get_system_role_repository)],
) -> MeOut:
    system_roles = await system_role_repository.list_system_roles(current_user.id)
    return MeOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        system_roles=[role.value for role in system_roles],
    )
