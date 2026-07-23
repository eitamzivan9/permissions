from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from permissions_server.api.deps import get_auth_service, get_current_user
from permissions_server.api.schemas.auth_schemas import LoginRequest, LoginResponse, MockUserOut
from permissions_server.application.auth_service import AuthService
from permissions_server.domain.entities import AuthenticatedUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/mock-users", response_model=list[MockUserOut])
async def list_mock_users(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> list[MockUserOut]:
    users = await auth_service.list_mock_users()
    return [MockUserOut(id=u.id, name=u.name, email=u.email) for u in users]


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    token = await auth_service.login(body.user_id)
    return LoginResponse(token=token)


@router.get("/me", response_model=MockUserOut)
async def get_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> MockUserOut:
    return MockUserOut(id=current_user.id, name=current_user.name, email=current_user.email)
