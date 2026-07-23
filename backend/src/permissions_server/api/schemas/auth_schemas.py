from __future__ import annotations

from pydantic import BaseModel


class MockUserOut(BaseModel):
    id: str
    name: str
    email: str


class LoginRequest(BaseModel):
    user_id: str


class LoginResponse(BaseModel):
    token: str
