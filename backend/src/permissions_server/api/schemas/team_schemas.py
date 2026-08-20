"""Wire schemas for api/routers/teams_router.py."""

from __future__ import annotations

from pydantic import BaseModel


class TeamOut(BaseModel):
    id: str
    name: str


class CreateTeamRequest(BaseModel):
    name: str


class TeamMemberOut(BaseModel):
    user_id: str
