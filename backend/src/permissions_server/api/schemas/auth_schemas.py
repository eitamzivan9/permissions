from __future__ import annotations

from pydantic import BaseModel


class MockUserOut(BaseModel):
    id: str
    name: str
    email: str


class MeOut(MockUserOut):
    """/auth/me only: who am I, plus system-wide roles the frontend needs to
    gate superuser-only affordances (e.g. 'Create team workspace')."""

    system_roles: list[str]


class LoginRequest(BaseModel):
    user_id: str


class LoginResponse(BaseModel):
    token: str
