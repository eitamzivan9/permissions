"""Wire schemas for api/routers/restrictions_router.py."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from permissions_server.domain.entities import Role

GranteeTypeLiteral = Literal["user", "team"]


class SetRestrictionRequest(BaseModel):
    role: Role


class RestrictionOut(BaseModel):
    grantee_type: GranteeTypeLiteral
    user_id: str | None
    team_id: str | None
    resource_id: str
    role: Role
    granted_by: str
