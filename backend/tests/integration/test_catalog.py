from tests.integration.conftest import auth_headers, login_as


def _find(items, resource_id):
    for item in items:
        if item["id"] == resource_id:
            return item
        found = _find(item["children"], resource_id)
        if found is not None:
            return found
    return None


async def test_catalog_requires_auth(client):
    resp = await client.get("/catalog")
    assert resp.status_code == 401


async def test_catalog_shows_full_tree_with_none_for_ungranted_user(client):
    # u031 (bottom-of-org IC) has no grants at all
    token = await login_as(client, "u031")
    resp = await client.get("/catalog", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1  # one seeded Workspace
    workspace = body["items"][0]
    assert workspace["id"] == "ws-city"
    assert workspace["effective_role"] is None
    assert workspace["can_manage"] is False

    map_item = _find(body["items"], "map-city-roads")
    assert map_item is not None
    assert map_item["effective_role"] is None


async def test_root_user_has_admin_from_bootstrap_seed(client):
    token = await login_as(client, "u001")
    resp = await client.get("/catalog", headers=auth_headers(token), params={"search": "City Roads"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    map_item = body["items"][0]
    assert map_item["effective_role"] == "admin"
    assert map_item["can_manage"] is True
    assert all(layer["effective_role"] == "admin" for layer in map_item["children"])


async def test_catalog_search_filters_by_name(client):
    token = await login_as(client, "u001")
    resp = await client.get(
        "/catalog", headers=auth_headers(token), params={"search": "zzz-nomatch"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
