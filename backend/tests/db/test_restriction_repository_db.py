"""Exercises SqlAlchemyRestrictionRepository against real Postgres — the
restriction twin of test_grant_repository_db.py, same grantee_key uniqueness
concern (uq_restriction_grantee_resource) but exercised for the whitelist
table instead."""

from __future__ import annotations

from permissions_server.domain.entities import Grantee, GranteeType, ResourceType, Role


async def _make_resource(resource_repo, name="Root"):
    return await resource_repo.create(type=ResourceType.WORKSPACE, name=name, parent_id=None)


async def test_upsert_restriction_creates_then_updates_role(resource_repo, restriction_repo):
    ws = await _make_resource(resource_repo)
    grantee = Grantee(GranteeType.USER, user_id="u001")

    created = await restriction_repo.upsert_restriction(grantee, ws.id, Role.VIEWER, granted_by="u000")
    assert created.role is Role.VIEWER

    updated = await restriction_repo.upsert_restriction(grantee, ws.id, Role.ADMIN, granted_by="u000")
    assert updated.role is Role.ADMIN

    all_restrictions = await restriction_repo.list_restrictions_for_resource(ws.id)
    assert len(all_restrictions) == 1
    assert all_restrictions[0].role is Role.ADMIN


async def test_list_restrictions_for_resource_ids_spans_multiple_resources(
    resource_repo, restriction_repo
):
    ws1 = await _make_resource(resource_repo, "A")
    ws2 = await _make_resource(resource_repo, "B")
    grantee = Grantee(GranteeType.USER, user_id="u001")
    await restriction_repo.upsert_restriction(grantee, ws1.id, Role.ADMIN, granted_by="u000")
    await restriction_repo.upsert_restriction(grantee, ws2.id, Role.VIEWER, granted_by="u000")

    result = await restriction_repo.list_restrictions_for_resource_ids([ws1.id, ws2.id])
    assert {r.resource_id for r in result} == {ws1.id, ws2.id}

    assert await restriction_repo.list_restrictions_for_resource_ids([]) == []


async def test_list_restrictions_for_grantees_filters_to_requested(resource_repo, restriction_repo):
    ws = await _make_resource(resource_repo)
    wanted = Grantee(GranteeType.USER, user_id="u001")
    other = Grantee(GranteeType.USER, user_id="u002")
    await restriction_repo.upsert_restriction(wanted, ws.id, Role.ADMIN, granted_by="u000")
    await restriction_repo.upsert_restriction(other, ws.id, Role.VIEWER, granted_by="u000")

    result = await restriction_repo.list_restrictions_for_grantees([wanted])
    assert [r.grantee for r in result] == [wanted]


async def test_delete_restriction_removes_only_that_grantee(resource_repo, restriction_repo):
    ws = await _make_resource(resource_repo)
    grantee = Grantee(GranteeType.USER, user_id="u001")
    other = Grantee(GranteeType.USER, user_id="u002")
    await restriction_repo.upsert_restriction(grantee, ws.id, Role.ADMIN, granted_by="u000")
    await restriction_repo.upsert_restriction(other, ws.id, Role.VIEWER, granted_by="u000")

    await restriction_repo.delete_restriction(grantee, ws.id)

    remaining = await restriction_repo.list_restrictions_for_resource(ws.id)
    assert [r.grantee for r in remaining] == [other]
    assert await restriction_repo.get_restriction(grantee, ws.id) is None


async def test_delete_restrictions_for_resource_ids_bulk_removes(resource_repo, restriction_repo):
    ws1 = await _make_resource(resource_repo, "A")
    ws2 = await _make_resource(resource_repo, "B")
    grantee = Grantee(GranteeType.USER, user_id="u001")
    await restriction_repo.upsert_restriction(grantee, ws1.id, Role.ADMIN, granted_by="u000")
    await restriction_repo.upsert_restriction(grantee, ws2.id, Role.ADMIN, granted_by="u000")

    await restriction_repo.delete_restrictions_for_resource_ids([ws1.id, ws2.id])

    assert await restriction_repo.list_restrictions_for_resource(ws1.id) == []
    assert await restriction_repo.list_restrictions_for_resource(ws2.id) == []

    # no-op, not an error, for an empty id list
    await restriction_repo.delete_restrictions_for_resource_ids([])
