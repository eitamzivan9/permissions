from permissions_server.domain.entities import SystemRole
from tests.integration.conftest import auth_headers, login_as

# Same org tree recap as test_grants.py: u001 is root (Admin via bootstrap
# seed on every top-level Workspace); u002 is a VP; u016 sits under u002;
# u024 sits under the *other* VP branch, not a subordinate of u002.
ROOT = "u001"
VP = "u002"
VP_SUBORDINATE = "u016"
OUTSIDER = "u024"

MAP_ID = "map-zoning"  # "Zoning Districts", under f-land-use -> ws-city
OTHER_MAP_ID = "map-parcels"  # "Property Parcels" -- kept restriction-free except where noted
TEAM_ID = "team-gis-analysts"


async def _grant_user(client, actor_token, resource_id, user_id, role):
    return await client.put(
        f"/grants/{resource_id}/user/{user_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def _restrict_user(client, actor_token, resource_id, user_id, role):
    return await client.put(
        f"/restrictions/{resource_id}/user/{user_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def _effective_role(client, token, query):
    catalog = await client.get("/catalog", headers=auth_headers(token), params={"q": query})
    return catalog.json()["items"][0]["effective_role"]


async def test_restriction_gates_unlisted_actor_including_the_setting_admin(client):
    root_token = await login_as(client, ROOT)
    resp = await _restrict_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")
    assert resp.status_code == 200

    sub_token = await login_as(client, VP_SUBORDINATE)
    assert await _effective_role(client, sub_token, "Zoning Districts") == "viewer"

    # root set the restriction without listing themselves -> now locked out,
    # even though they were Admin (via bootstrap) a moment ago.
    assert await _effective_role(client, root_token, "Zoning Districts") is None

    outsider_token = await login_as(client, OUTSIDER)
    assert await _effective_role(client, outsider_token, "Zoning Districts") is None


async def test_locked_out_admin_cannot_manage_further_restrictions(client):
    """No self-lockout guard, by design: once root's own restriction excludes
    them, they've lost Admin there and can't even fix it themselves anymore."""
    root_token = await login_as(client, ROOT)
    await _restrict_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")

    followup = await _restrict_user(client, root_token, MAP_ID, OUTSIDER, "viewer")
    assert followup.status_code == 403


async def test_super_editor_bypasses_restriction(client):
    root_token = await login_as(client, ROOT)
    await _restrict_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")

    await client.app_state.system_role_repository.grant_system_role(
        OUTSIDER, SystemRole.SUPER_EDITOR, granted_by="test"
    )
    outsider_token = await login_as(client, OUTSIDER)
    assert await _effective_role(client, outsider_token, "Zoning Districts") == "admin"


async def test_super_viewer_bypasses_restriction(client):
    root_token = await login_as(client, ROOT)
    await _restrict_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")

    await client.app_state.system_role_repository.grant_system_role(
        OUTSIDER, SystemRole.SUPER_VIEWER, granted_by="test"
    )
    outsider_token = await login_as(client, OUTSIDER)
    assert await _effective_role(client, outsider_token, "Zoning Districts") == "viewer"


async def test_manager_cannot_set_restriction(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "manager")

    vp_token = await login_as(client, VP)
    resp = await _restrict_user(client, vp_token, MAP_ID, VP_SUBORDINATE, "viewer")
    assert resp.status_code == 403


async def test_restriction_on_user_requires_org_chart_check(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "admin")

    vp_token = await login_as(client, VP)
    # OUTSIDER (u024) is not VP's subordinate -- Admin rank alone isn't enough.
    resp = await _restrict_user(client, vp_token, MAP_ID, OUTSIDER, "viewer")
    assert resp.status_code == 403


async def test_restriction_on_team_skips_org_chart_check(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "admin")

    vp_token = await login_as(client, VP)
    resp = await client.put(
        f"/restrictions/{MAP_ID}/team/{TEAM_ID}",
        headers=auth_headers(vp_token),
        json={"role": "editor"},
    )
    assert resp.status_code == 200


async def test_restriction_tie_break_is_rank_based_not_recency(client):
    root_token = await login_as(client, ROOT)
    # High-rank entry set FIRST, low-rank entry set LAST -- if "last wins"
    # were implemented (explicitly rejected), this would resolve to viewer.
    await _restrict_user(client, root_token, MAP_ID, VP_SUBORDINATE, "admin")
    await client.put(
        f"/restrictions/{MAP_ID}/team/team-north-ops",
        headers=auth_headers(root_token),
        json={"role": "viewer"},
    )
    # VP_SUBORDINATE (u016) is also a member of team-north-ops per seed data.
    sub_token = await login_as(client, VP_SUBORDINATE)
    assert await _effective_role(client, sub_token, "Zoning Districts") == "admin"


async def test_list_restrictions_requires_admin(client):
    root_token = await login_as(client, ROOT)
    resp = await client.get(f"/restrictions/{OTHER_MAP_ID}", headers=auth_headers(root_token))
    assert resp.status_code == 200
    assert resp.json() == []

    outsider_token = await login_as(client, OUTSIDER)
    resp = await client.get(f"/restrictions/{OTHER_MAP_ID}", headers=auth_headers(outsider_token))
    assert resp.status_code == 403


async def test_delete_restriction_removes_the_gate(client):
    """A USER-grantee restriction can never name the setting admin themselves
    ('manager of self' is false in the org chart, same as ordinary grants) --
    so root locks itself out here, and only a superuser can clean it up. This
    doubles as the documented recovery path for the self-lockout scenario."""
    root_token = await login_as(client, ROOT)
    await _restrict_user(client, root_token, OTHER_MAP_ID, VP_SUBORDINATE, "viewer")

    outsider_token = await login_as(client, OUTSIDER)
    assert await _effective_role(client, outsider_token, "Property Parcels") is None
    assert await _effective_role(client, root_token, "Property Parcels") is None

    await client.app_state.system_role_repository.grant_system_role(
        OUTSIDER, SystemRole.SUPER_EDITOR, granted_by="test"
    )
    super_token = await login_as(client, OUTSIDER)
    del_resp = await client.delete(
        f"/restrictions/{OTHER_MAP_ID}/user/{VP_SUBORDINATE}", headers=auth_headers(super_token)
    )
    assert del_resp.status_code == 204

    # gate fully lifted -> root's bootstrap Admin grant resolves normally again
    assert await _effective_role(client, root_token, "Property Parcels") == "admin"
