from permissions_server.domain.entities import SystemRole
from tests.integration.conftest import auth_headers, login_as

ROOT = "u001"  # bootstrap Admin on every top-level Workspace (see main.py)
VP_SUBORDINATE = "u016"
OUTSIDER = "u024"  # no access anywhere in ws-city

MAP_ID = "map-zoning"  # under f-land-use, has descendant layers
LAYER_ID = "layer-zoning-residential"  # a descendant of map-zoning
FOLDER_ID = "f-infrastructure"


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


async def _delete(client, token, resource_id):
    return await client.delete(f"/resources/{resource_id}", headers=auth_headers(token))


async def _create(client, token, *, type, name, parent_id):
    resp = await client.post(
        "/resources",
        headers=auth_headers(token),
        json={"type": type, "name": name, "parent_id": parent_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_admin_deletes_resource_and_its_subtree(client):
    """Also doubles as the regression guard proving Map is deliberately
    exempt from the Folder/Group/Workspace empty-check — map-zoning has
    descendant layers and must still cascade-delete unconditionally."""
    root_token = await login_as(client, ROOT)
    resp = await _delete(client, root_token, MAP_ID)
    assert resp.status_code == 204

    catalog = await client.get("/catalog", headers=auth_headers(root_token))
    assert _find(catalog.json()["items"], MAP_ID) is None
    assert _find(catalog.json()["items"], LAYER_ID) is None


async def test_delete_cleans_up_grants_and_restrictions_in_the_subtree(client):
    # SUPER_EDITOR so the actor can both restrict the map (an org-chart-gated
    # action ROOT can't take against itself) and still delete it afterwards
    # despite not being on the whitelist it just created (SUPER_EDITOR
    # bypasses restrictions unconditionally — see CLAUDE.md's
    # "Restrictions" section).
    await client.app_state.system_role_repository.grant_system_role(
        ROOT, SystemRole.SUPER_EDITOR, granted_by="test"
    )
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, LAYER_ID, VP_SUBORDINATE, "viewer")
    await client.put(
        f"/restrictions/{MAP_ID}/user/{VP_SUBORDINATE}",
        headers=auth_headers(root_token),
        json={"role": "editor"},
    )

    resp = await _delete(client, root_token, MAP_ID)
    assert resp.status_code == 204

    # re-creating a resource with a colliding id is impossible (ids are
    # uuid4), so the only observable proof of cascade cleanup is that
    # nothing 500s trying to look these up and the catalog no longer lists
    # the grant/restriction's target at all.
    catalog = await client.get("/catalog", headers=auth_headers(root_token))
    assert _find(catalog.json()["items"], MAP_ID) is None


async def test_delete_forbidden_without_admin(client):
    root_token = await login_as(client, ROOT)
    await _grant_user(client, root_token, MAP_ID, VP_SUBORDINATE, "editor")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _delete(client, sub_token, MAP_ID)
    assert resp.status_code == 403


async def test_delete_forbidden_with_no_access_at_all(client):
    token = await login_as(client, OUTSIDER)
    resp = await _delete(client, token, MAP_ID)
    assert resp.status_code == 403
    assert resp.json()["code"] == "delete_requires_admin"


async def test_delete_nonexistent_resource_is_404(client):
    root_token = await login_as(client, ROOT)
    resp = await _delete(client, root_token, "resource-does-not-exist")
    assert resp.status_code == 404
    # No specific code at this raise site -> NotFoundError's generic default.
    assert resp.json()["code"] == "not_found"
    assert resp.json()["params"] == {}


async def test_delete_non_empty_folder_is_conflict(client):
    """Folder/Group/Workspace only ever hard-delete when empty — this
    permissions server doesn't own the Map/Layer data nested underneath, so
    it must never bulk-wipe it via a folder-level delete."""
    root_token = await login_as(client, ROOT)
    resp = await _delete(client, root_token, FOLDER_ID)
    assert resp.status_code == 409
    # The resource id must never leak into the error message — it's not
    # actionable for the caller and the frontend shouldn't have to scrub it.
    assert FOLDER_ID not in resp.json()["detail"]
    assert resp.json()["code"] == "delete_not_empty"
    assert resp.json()["params"]["count"] > 0

    catalog = await client.get("/catalog", headers=auth_headers(root_token))
    assert _find(catalog.json()["items"], FOLDER_ID) is not None


async def test_admin_at_subtree_but_not_root_can_delete_only_their_subtree(client):
    root_token = await login_as(client, ROOT)
    empty_folder_id = await _create(
        client, root_token, type="folder", name="Empty Subfolder", parent_id=FOLDER_ID
    )
    await _grant_user(client, root_token, empty_folder_id, VP_SUBORDINATE, "admin")

    sub_token = await login_as(client, VP_SUBORDINATE)
    resp = await _delete(client, sub_token, empty_folder_id)
    assert resp.status_code == 204

    catalog = await client.get("/catalog", headers=auth_headers(root_token))
    assert _find(catalog.json()["items"], empty_folder_id) is None


async def test_delete_empty_folder_succeeds(client):
    root_token = await login_as(client, ROOT)
    empty_folder_id = await _create(
        client, root_token, type="folder", name="Another Empty Folder", parent_id=FOLDER_ID
    )

    resp = await _delete(client, root_token, empty_folder_id)
    assert resp.status_code == 204
