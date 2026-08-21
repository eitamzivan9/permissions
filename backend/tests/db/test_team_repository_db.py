"""Exercises SqlAlchemyTeamRepository against real Postgres, including the
team_memberships join used by list_teams_for_user."""

from __future__ import annotations


async def test_create_and_get_by_id(team_repo):
    team = await team_repo.create("Geo Team")
    assert team.name == "Geo Team"
    assert (await team_repo.get_by_id(team.id)).name == "Geo Team"
    assert await team_repo.get_by_id("no-such-team") is None


async def test_list_page_filters_by_search(team_repo):
    await team_repo.create("Infrastructure")
    await team_repo.create("Land Use")

    page = await team_repo.list_page(search="infra", page=1, page_size=10)
    assert [t.name for t in page.items] == ["Infrastructure"]
    assert page.total == 1


async def test_add_member_then_list_members_and_teams_for_user(team_repo):
    team = await team_repo.create("Geo Team")
    await team_repo.add_member(team.id, "u001")
    await team_repo.add_member(team.id, "u002")

    assert await team_repo.list_members(team.id) == ["u001", "u002"]
    teams_for_u001 = await team_repo.list_teams_for_user("u001")
    assert [t.id for t in teams_for_u001] == [team.id]


async def test_add_member_is_idempotent(team_repo):
    team = await team_repo.create("Geo Team")
    await team_repo.add_member(team.id, "u001")
    await team_repo.add_member(team.id, "u001")  # must not raise a unique-constraint error

    assert await team_repo.list_members(team.id) == ["u001"]


async def test_remove_member(team_repo):
    team = await team_repo.create("Geo Team")
    await team_repo.add_member(team.id, "u001")
    await team_repo.remove_member(team.id, "u001")

    assert await team_repo.list_members(team.id) == []
    # removing again is a no-op, not an error
    await team_repo.remove_member(team.id, "u001")
