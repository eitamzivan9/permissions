from tests.integration.conftest import auth_headers, login_as

ROOT = "u001"
VP_SUBORDINATE = "u016"
OUTSIDER = "u024"

MAP_ID = "map-zoning"  # under f-land-use
DEST_FOLDER_ID = "f-infrastructure"
SOURCE_FOLDER_ID = "f-land-use"
LAYER_ID = "layer-zoning-residential"  # a descendant of map-zoning


def _find(items, resource_id):
    for item in items:
        if item["id"] == resource_id:
            return item
        found = _find(item["children"], resource_id)
        if found is not None:
            return found
    return None


async def _grant_user(client, actor_token, resource_id, user_id, role):
    return await client.put(
        f"/grants/{resource_id}/user/{user_id}",
        headers=auth_headers(actor_token),
        json={"role": role},
    )


async def _move(client, token, resource_id, new_parent_id):
    return await client.patch(
        f"/resources/{resource_id}/move",
        headers=auth_headers(token),
        json={"new_parent_id": new_parent_id},
    )


async def test_admin_at_source_and_editor_at_destination_can_move_with_subtree(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "admin")
    await _grant_user(client, root_token, DEST_FOLDER_ID, VP_SUBORDINATE, "editor")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _move(client, sub_token, MAP_ID, DEST_FOLDER_ID)
    assert resp.status_code == 200
    assert resp.json()["parent_id"] == DEST_FOLDER_ID

    catalog = await client.get("/catalog", headers=auth_headers(root_token))
    dest_folder = _find(catalog.json()["items"], DEST_FOLDER_ID)
    assert _find(dest_folder["children"], MAP_ID) is not None

    source_folder = _find(catalog.json()["items"], SOURCE_FOLDER_ID)
    assert _find(source_folder["children"], MAP_ID) is None

    # the whole subtree came along, still nested under the moved map
    moved_map = _find(dest_folder["children"], MAP_ID)
    assert _find(moved_map["children"], LAYER_ID) is not None


async def test_move_forbidden_without_admin_at_source(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "editor")
    await _grant_user(client, root_token, DEST_FOLDER_ID, VP_SUBORDINATE, "editor")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _move(client, sub_token, MAP_ID, DEST_FOLDER_ID)
    assert resp.status_code == 403
    assert resp.json()["code"] == "move_requires_admin"


async def test_move_forbidden_without_editor_at_destination(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "admin")
    await _grant_user(client, root_token, DEST_FOLDER_ID, VP_SUBORDINATE, "viewer")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _move(client, sub_token, MAP_ID, DEST_FOLDER_ID)
    assert resp.status_code == 403
    assert resp.json()["code"] == "move_destination_requires_editor"


async def test_move_forbidden_with_no_access_at_all(client):
    token = await login_as(client, OUTSIDER)
    resp = await _move(client, token, MAP_ID, DEST_FOLDER_ID)
    assert resp.status_code == 403


async def test_move_into_invalid_type_pair_is_conflict(client):
    root_token = await login_as(client, ROOT)
    resp = await _move(client, root_token, MAP_ID, "layer-roads-bike")
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "invalid_child_type"
    assert body["params"] == {"child": "map", "parent": "layer"}


async def test_move_into_own_subtree_is_conflict(client):
    root_token = await login_as(client, ROOT)
    # f-hazards is currently nested inside f-environment (folders nest) --
    # moving f-environment under its own child f-hazards would be a cycle.
    resp = await _move(client, root_token, "f-environment", "f-hazards")
    assert resp.status_code == 409
    assert resp.json()["code"] == "move_into_own_subtree"


async def test_move_to_nonexistent_destination_is_404(client):
    root_token = await login_as(client, ROOT)
    resp = await _move(client, root_token, MAP_ID, "resource-does-not-exist")
    assert resp.status_code == 404


async def test_move_of_nonexistent_resource_is_404(client):
    root_token = await login_as(client, ROOT)
    resp = await _move(client, root_token, "resource-does-not-exist", DEST_FOLDER_ID)
    assert resp.status_code == 404


async def test_restricted_destination_blocks_the_move(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "admin")
    await _grant_user(client, root_token, DEST_FOLDER_ID, VP_SUBORDINATE, "editor")
    # restrict the destination to someone else -> VP_SUBORDINATE loses Editor there
    await client.put(
        f"/restrictions/{DEST_FOLDER_ID}/user/{OUTSIDER}",
        headers=auth_headers(root_token),
        json={"role": "editor"},
    )

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _move(client, sub_token, MAP_ID, DEST_FOLDER_ID)
    assert resp.status_code == 403
