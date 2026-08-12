from tests.integration.conftest import auth_headers, login_as

# Org tree recap (mock_users.json): u001 is root (manager of everyone).
# u002 is a VP; u016 sits under u002 (u002->u004->u008->u016); u024 sits
# under the *other* VP, u003 (u003->u006->u012->u024) -- not a subordinate
# of u002, used to prove delegation is rejected across branches.
ROOT = "u001"
VP = "u002"
VP_SUBORDINATE = "u016"
NOT_VP_SUBORDINATE = "u024"

MAP_ID = "map-zoning"
CITY_ROADS_MAP_ID = "map-city-roads"
BIKE_LAYER_ID = "layer-roads-bike"
HIGHWAYS_LAYER_ID = "layer-roads-highways"
TEAM_ID = "team-gis-analysts"


async def _grant_user(client, actor_token, resource_id, user_id, role):
    return await client.put(
        f"/grants/{resource_id}/user/{user_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def _grant_team(client, actor_token, resource_id, team_id, role):
    return await client.put(
        f"/grants/{resource_id}/team/{team_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def test_manageable_users_lists_only_subordinates(client):
    token = await login_as(client, VP)
    resp = await client.get("/grants/manageable-users", headers=auth_headers(token))
    assert resp.status_code == 200
    ids = {u["id"] for u in resp.json()}
    assert VP_SUBORDINATE in ids
    assert NOT_VP_SUBORDINATE not in ids
    assert VP not in ids  # not your own manager relationship


async def test_grant_without_manager_role_is_forbidden(client):
    # u002 has no grants at all yet -> cannot delegate anything
    token = await login_as(client, VP)
    resp = await _grant_user(client, token, MAP_ID, VP_SUBORDINATE, "viewer")
    assert resp.status_code == 403


async def test_personal_workspace_owner_can_grant_to_a_non_subordinate(client):
    """The org-chart delegation check exists for shared resources managed by
    reporting-line authority; it doesn't fit a user's own personal sandbox,
    where the owner should be able to invite anyone. NOT_VP_SUBORDINATE is
    deliberately not VP's subordinate elsewhere in this file."""
    token = await login_as(client, VP)
    workspace = await client.get("/resources/my-workspace", headers=auth_headers(token))
    assert workspace.status_code == 200
    workspace_id = workspace.json()["id"]

    resp = await _grant_user(client, token, workspace_id, NOT_VP_SUBORDINATE, "editor")
    assert resp.status_code == 200

    manageable = await client.get(
        "/grants/manageable-users",
        headers=auth_headers(token),
        params={"resource_id": workspace_id},
    )
    assert NOT_VP_SUBORDINATE in {u["id"] for u in manageable.json()}


async def test_root_can_delegate_then_vp_can_delegate_to_own_subordinate(client):
    root_token = await login_as(client, ROOT)
    resp = await _grant_user(client, root_token, MAP_ID, VP, "manager")
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"

    vp_token = await login_as(client, VP)
    resp = await _grant_user(client, vp_token, MAP_ID, VP_SUBORDINATE, "viewer")
    assert resp.status_code == 200
    assert resp.json()["role"] == "viewer"

    sub_token = await login_as(client, VP_SUBORDINATE)
    catalog = await client.get(
        "/catalog", headers=auth_headers(sub_token), params={"q": "Zoning Districts"}
    )
    assert catalog.json()["items"][0]["effective_role"] == "viewer"


async def test_delegation_forbidden_across_org_branches(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "manager")

    vp_token = await login_as(client, VP)
    resp = await _grant_user(client, vp_token, MAP_ID, NOT_VP_SUBORDINATE, "viewer")
    assert resp.status_code == 403


async def test_manager_cannot_grant_manager_or_admin(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "manager")

    vp_token = await login_as(client, VP)
    resp = await _grant_user(client, vp_token, MAP_ID, VP_SUBORDINATE, "manager")
    assert resp.status_code == 403


async def test_team_grant_skips_org_chart_check(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP, "manager")

    vp_token = await login_as(client, VP)
    # NOT_VP_SUBORDINATE is not VP's subordinate, but a Team grant has no
    # org-chart requirement at all — only role rank matters.
    resp = await _grant_team(client, vp_token, MAP_ID, TEAM_ID, "editor")
    assert resp.status_code == 200
    assert resp.json()["role"] == "editor"
    assert resp.json()["team_id"] == TEAM_ID


async def test_layer_override_then_delete_reverts_to_map_default(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, CITY_ROADS_MAP_ID, VP, "manager")

    vp_token = await login_as(client, VP)
    await _grant_user(client, vp_token, CITY_ROADS_MAP_ID, VP_SUBORDINATE, "viewer")
    # nearer override on one layer, despite the map-level viewer default
    override_resp = await _grant_user(
        client, vp_token, BIKE_LAYER_ID, VP_SUBORDINATE, "editor"
    )
    assert override_resp.status_code == 200

    sub_token = await login_as(client, VP_SUBORDINATE)
    catalog = await client.get(
        "/catalog", headers=auth_headers(sub_token), params={"q": "City Roads"}
    )
    layers = {l["id"]: l["effective_role"] for l in catalog.json()["items"][0]["children"]}
    assert layers[BIKE_LAYER_ID] == "editor"
    assert layers[HIGHWAYS_LAYER_ID] == "viewer"

    delete_resp = await client.delete(
        f"/grants/{BIKE_LAYER_ID}/user/{VP_SUBORDINATE}", headers=auth_headers(vp_token)
    )
    assert delete_resp.status_code == 204

    catalog_after = await client.get(
        "/catalog", headers=auth_headers(sub_token), params={"q": "City Roads"}
    )
    layers_after = {
        l["id"]: l["effective_role"] for l in catalog_after.json()["items"][0]["children"]
    }
    assert layers_after[BIKE_LAYER_ID] == "viewer"


async def test_revoke_without_manager_role_is_forbidden(client):
    # root (Admin via bootstrap seed) grants VP_SUBORDINATE directly, so
    # there's an existing grant for VP (who has no permissions at all here)
    # to unsuccessfully try to revoke.
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")

    token = await login_as(client, VP)
    resp = await client.delete(
        f"/grants/{MAP_ID}/user/{VP_SUBORDINATE}", headers=auth_headers(token)
    )
    assert resp.status_code == 403


async def test_revoke_of_nonexistent_grant_is_a_noop(client):
    token = await login_as(client, VP)  # VP has no permissions at all here
    resp = await client.delete(
        f"/grants/{MAP_ID}/user/{VP_SUBORDINATE}", headers=auth_headers(token)
    )
    assert resp.status_code == 204


async def test_grant_target_of_nonexistent_resource_is_404(client):
    root_token = await login_as(client, ROOT)
    resp = await _grant_user(client, root_token, "resource-does-not-exist", VP, "editor")
    assert resp.status_code == 404


async def test_user_can_revoke_their_own_grant_without_any_manage_authority(client):
    """'Remove access' (frontend) must work for an ordinary Viewer with no
    Manager/Admin role and no org-chart authority over anyone — dropping
    your OWN access is never delegation."""
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "viewer")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await client.delete(
        f"/grants/{MAP_ID}/user/{VP_SUBORDINATE}", headers=auth_headers(sub_token)
    )
    assert resp.status_code == 204

    catalog = await client.get(
        "/catalog", headers=auth_headers(sub_token), params={"q": "Zoning Districts"}
    )
    assert catalog.json()["items"][0]["effective_role"] is None
