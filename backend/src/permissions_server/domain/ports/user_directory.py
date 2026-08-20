"""Looks up user identities — mocked now, real AD/ADFS later."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import AuthenticatedUser


class UserDirectory(Protocol):
    """Looks up identities. Backed by mock_users.json now, real AD/ADFS later."""

    async def get_user(self, user_id: str) -> AuthenticatedUser | None: ...

    async def list_users(self) -> list[AuthenticatedUser]: ...

    async def search_users(self, query: str) -> list[AuthenticatedUser]: ...
