from permissions_server.domain.entities import SystemRole
from tests.integration.conftest import auth_headers, login_as

ROOT = "u001"  # bootstrap Admin on every top-level Workspace (see main.py)
VP = "u002"
VP_SUBORDINATE = "u016"
OUTSIDER = "u024"  # no access anywhere in ws-city

WORKSPACE_ID = "ws-city"
FOLDER_ID = "f-infrastructure"


async def _grant_user(client, actor_token, resource_id, user_id, role):
    return await client.put(
        f"/grants/{resource_id}/user/{user_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def _create_resource(client, token, *, type, name, parent_id):
    return await client.post(
        "/resources",
        headers=auth_headers(token),
        json={"type": type, "name": name, "parent_id": parent_id},
    )


async def test_create_child_under_editor_parent_makes_creator_admin(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, FOLDER_ID, VP_SUBORDINATE, "editor")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _create_resource(
        client, sub_token, type="map", name="Sandbox Map", parent_id=FOLDER_ID
    )
    assert resp.status_code == 201
    new_id = resp.json()["id"]
    assert resp.json()["parent_id"] == FOLDER_ID

    grants = await client.get(f"/grants/{new_id}", headers=auth_headers(sub_token))
    roles = {g["user_id"]: g["role"] for g in grants.json() if g["grantee_type"] == "user"}
    assert roles[VP_SUBORDINATE] == "admin"


async def test_create_child_with_only_viewer_at_parent_is_forbidden(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, FOLDER_ID, VP_SUBORDINATE, "viewer")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _create_resource(
        client, sub_token, type="map", name="Nope", parent_id=FOLDER_ID
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "create_requires_editor"


async def test_create_child_with_no_access_at_parent_is_forbidden(client):
    token = await login_as(client, OUTSIDER)
    resp = await _create_resource(client, token, type="map", name="Nope", parent_id=FOLDER_ID)
    assert resp.status_code == 403


async def test_create_child_with_invalid_type_pair_is_conflict(client):
    root_token = await login_as(client, ROOT)
    resp = await _create_resource(
        client, root_token, type="map", name="Bad", parent_id="layer-roads-bike"
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_child_type"


async def test_create_child_under_nonexistent_parent_is_404(client):
    root_token = await login_as(client, ROOT)
    resp = await _create_resource(
        client, root_token, type="folder", name="Nope", parent_id="resource-does-not-exist"
    )
    assert resp.status_code == 404


async def test_my_workspace_is_idempotent_and_creator_is_admin(client):
    token = await login_as(client, VP_SUBORDINATE)
    first = await client.get("/resources/my-workspace", headers=auth_headers(token))
    assert first.status_code == 200
    assert first.json()["type"] == "workspace"
    assert first.json()["owner_id"] == VP_SUBORDINATE

    second = await client.get("/resources/my-workspace", headers=auth_headers(token))
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    grants = await client.get(f"/grants/{first.json()['id']}", headers=auth_headers(token))
    roles = {g["user_id"]: g["role"] for g in grants.json() if g["grantee_type"] == "user"}
    assert roles[VP_SUBORDINATE] == "admin"


async def test_my_workspace_is_distinct_per_user(client):
    token_a = await login_as(client, VP_SUBORDINATE)
    token_b = await login_as(client, OUTSIDER)
    ws_a = await client.get("/resources/my-workspace", headers=auth_headers(token_a))
    ws_b = await client.get("/resources/my-workspace", headers=auth_headers(token_b))
    assert ws_a.json()["id"] != ws_b.json()["id"]


async def test_create_team_workspace_requires_super_editor(client):
    token = await login_as(client, VP)
    resp = await client.post(
        "/resources/workspaces",
        headers=auth_headers(token),
        json={"name": "New Team Workspace", "admin_user_id": VP},
    )
    assert resp.status_code == 403


async def test_super_editor_creates_team_workspace_with_named_admin(client):
    await client.app_state.system_role_repository.grant_system_role(
        ROOT, SystemRole.SUPER_EDITOR, granted_by="test"
    )
    token = await login_as(client, ROOT)
    resp = await client.post(
        "/resources/workspaces",
        headers=auth_headers(token),
        json={"name": "New Team Workspace", "admin_user_id": VP_SUBORDINATE},
    )
    assert resp.status_code == 201
    new_id = resp.json()["id"]
    assert resp.json()["parent_id"] is None
    assert resp.json()["owner_id"] is None

    grants = await client.get(f"/grants/{new_id}", headers=auth_headers(token))
    roles = {g["user_id"]: g["role"] for g in grants.json() if g["grantee_type"] == "user"}
    # the NAMED admin, not the superuser who created it, ends up Admin
    assert roles.get(VP_SUBORDINATE) == "admin"
    assert ROOT not in roles


async def test_hebrew_resource_name_round_trips_through_create_and_search(client):
    """UI data can be in Hebrew — names are stored and searched as-is (UTF-8),
    never translated or mangled."""
    root_token = await login_as(client, ROOT)
    hebrew_name = "תכנון עירוני 2026"
    resp = await _create_resource(
        client, root_token, type="folder", name=hebrew_name, parent_id=WORKSPACE_ID
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == hebrew_name

    search = await client.get(
        "/catalog", headers=auth_headers(root_token), params={"search": "עירוני"}
    )
    assert search.status_code == 200

    def names(items):
        for item in items:
            yield item["name"]
            yield from names(item["children"])

    assert hebrew_name in set(names(search.json()["items"]))
