from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from permissions_server.api.deps import get_current_user, get_team_repository
from permissions_server.api.schemas.team_schemas import CreateTeamRequest, TeamMemberOut, TeamOut
from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.ports.team_repository import TeamRepository

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
async def list_teams(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> list[TeamOut]:
    page = await team_repository.list_page(search=None, page=1, page_size=1000)
    return [TeamOut(id=t.id, name=t.name) for t in page.items]


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: CreateTeamRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> TeamOut:
    team = await team_repository.create(body.name)
    return TeamOut(id=team.id, name=team.name)


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
async def list_team_members(
    team_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> list[TeamMemberOut]:
    member_ids = await team_repository.list_members(team_id)
    return [TeamMemberOut(user_id=uid) for uid in member_ids]


@router.post("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_team_member(
    team_id: str,
    user_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> Response:
    await team_repository.add_member(team_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    team_repository: Annotated[TeamRepository, Depends(get_team_repository)],
) -> Response:
    await team_repository.remove_member(team_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
