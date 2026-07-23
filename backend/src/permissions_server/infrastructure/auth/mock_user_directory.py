from __future__ import annotations

from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.infrastructure.auth._mock_users_fixture import load_mock_users


class MockUserDirectory:
    async def get_user(self, user_id: str) -> AuthenticatedUser | None:
        for record in load_mock_users():
            if record["id"] == user_id:
                return AuthenticatedUser(
                    id=record["id"], name=record["name"], email=record["email"]
                )
        return None

    async def list_users(self) -> list[AuthenticatedUser]:
        return [
            AuthenticatedUser(id=r["id"], name=r["name"], email=r["email"])
            for r in load_mock_users()
        ]

    async def search_users(self, query: str) -> list[AuthenticatedUser]:
        q = query.lower()
        return [
            AuthenticatedUser(id=r["id"], name=r["name"], email=r["email"])
            for r in load_mock_users()
            if q in r["name"].lower() or q in r["email"].lower()
        ]
