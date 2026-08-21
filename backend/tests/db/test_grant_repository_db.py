"""Exercises SqlAlchemyGrantRepository against real Postgres — in particular
the grantee_key uniqueness constraint (uq_grant_grantee_resource), which only
the real schema enforces; the in-memory repository can't exhibit its
absence/presence at all."""

from __future__ import annotations

from permissions_server.domain.entities import Grantee, GranteeType, ResourceType, Role


async def _make_resource(resource_repo, name="Root"):
    return await resource_repo.create(type=ResourceType.WORKSPACE, name=name, parent_id=None)


async def test_upsert_grant_creates_then_updates_role(resource_repo, grant_repo):
    ws = await _make_resource(resource_repo)
    grantee = Grantee(GranteeType.USER, user_id="u001")

    created = await grant_repo.upsert_grant(grantee, ws.id, Role.EDITOR, granted_by="u000")
    assert created.role is Role.EDITOR

    updated = await grant_repo.upsert_grant(grantee, ws.id, Role.ADMIN, granted_by="u000")
    assert updated.role is Role.ADMIN

    all_grants = await grant_repo.list_grants_for_resource(ws.id)
    assert len(all_grants) == 1
    assert all_grants[0].role is Role.ADMIN


async def test_user_and_team_grantees_on_same_resource_coexist(resource_repo, grant_repo, team_repo):
    # Regression check for the exact reason grantee_key exists: a plain
    # UNIQUE(grantee_type, user_id, team_id, resource_id) wouldn't reliably
    # distinguish two USER grants (both team_id NULL) — this asserts two
    # *different* grantee kinds at the same resource aren't merged/clobbered.
    ws = await _make_resource(resource_repo)
    team = await team_repo.create("Geo Team")  # permission_grants.team_id is a real FK
    user_grantee = Grantee(GranteeType.USER, user_id="u001")
    team_grantee = Grantee(GranteeType.TEAM, team_id=team.id)

    await grant_repo.upsert_grant(user_grantee, ws.id, Role.EDITOR, granted_by="u000")
    await grant_repo.upsert_grant(team_grantee, ws.id, Role.VIEWER, granted_by="u000")

    grants = await grant_repo.list_grants_for_resource(ws.id)
    assert {g.grantee for g in grants} == {user_grantee, team_grantee}


async def test_list_grants_for_grantees_filters_to_requested(resource_repo, grant_repo):
    ws = await _make_resource(resource_repo)
    wanted = Grantee(GranteeType.USER, user_id="u001")
    other = Grantee(GranteeType.USER, user_id="u002")
    await grant_repo.upsert_grant(wanted, ws.id, Role.EDITOR, granted_by="u000")
    await grant_repo.upsert_grant(other, ws.id, Role.VIEWER, granted_by="u000")

    result = await grant_repo.list_grants_for_grantees([wanted])
    assert [g.grantee for g in result] == [wanted]

    assert await grant_repo.list_grants_for_grantees([]) == []


async def test_delete_grant_removes_only_that_grantee(resource_repo, grant_repo):
    ws = await _make_resource(resource_repo)
    grantee = Grantee(GranteeType.USER, user_id="u001")
    other = Grantee(GranteeType.USER, user_id="u002")
    await grant_repo.upsert_grant(grantee, ws.id, Role.EDITOR, granted_by="u000")
    await grant_repo.upsert_grant(other, ws.id, Role.VIEWER, granted_by="u000")

    await grant_repo.delete_grant(grantee, ws.id)

    remaining = await grant_repo.list_grants_for_resource(ws.id)
    assert [g.grantee for g in remaining] == [other]
    assert await grant_repo.get_grant(grantee, ws.id) is None


async def test_delete_grants_for_resource_ids_bulk_removes(resource_repo, grant_repo):
    ws1 = await _make_resource(resource_repo, "A")
    ws2 = await _make_resource(resource_repo, "B")
    grantee = Grantee(GranteeType.USER, user_id="u001")
    await grant_repo.upsert_grant(grantee, ws1.id, Role.EDITOR, granted_by="u000")
    await grant_repo.upsert_grant(grantee, ws2.id, Role.EDITOR, granted_by="u000")

    await grant_repo.delete_grants_for_resource_ids([ws1.id, ws2.id])

    assert await grant_repo.list_grants_for_resource(ws1.id) == []
    assert await grant_repo.list_grants_for_resource(ws2.id) == []

    # no-op, not an error, for an empty id list
    await grant_repo.delete_grants_for_resource_ids([])
