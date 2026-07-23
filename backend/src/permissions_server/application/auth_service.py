"""Mock login. 'Who am I' needs no service call — api/deps.py's
get_current_user() already resolves a full AuthenticatedUser from the
validated token, so the /auth/me router returns that directly."""

from __future__ import annotations

from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.errors import NotFoundError
from permissions_server.domain.ports.token_issuer import TokenIssuer
from permissions_server.domain.ports.user_directory import UserDirectory


class AuthService:
    def __init__(
        self, user_directory: UserDirectory, token_issuer: TokenIssuer
    ) -> None:
        self._user_directory = user_directory
        self._token_issuer = token_issuer

    async def list_mock_users(self) -> list[AuthenticatedUser]:
        return await self._user_directory.list_users()

    async def login(self, user_id: str) -> str:
        user = await self._user_directory.get_user(user_id)
        if user is None:
            raise NotFoundError(f"no mock user with id {user_id}")
        return await self._token_issuer.issue(user)
