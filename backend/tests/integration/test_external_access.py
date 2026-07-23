from tests.integration.conftest import auth_headers, login_as

ROOT = "u001"
VP = "u002"
MAP_ID = "map-zoning"


async def test_external_access_requires_auth(client):
    resp = await client.get("/external/v1/my-access")
    assert resp.status_code == 401


async def test_external_access_filters_out_none_but_totals_all_maps(client):
    root_token = await login_as(client, ROOT)
    await client.put(
        f"/grants/{MAP_ID}/user/{VP}",
        headers=auth_headers(root_token),
        json={"role": "editor"},
    )

    vp_token = await login_as(client, VP)
    resp = await client.get(
        "/external/v1/my-access", headers=auth_headers(vp_token), params={"page_size": 50}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10  # pagination universe is all maps, not the filtered count
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == MAP_ID
    assert body["items"][0]["role"] == "editor"


async def test_external_access_is_empty_for_ungranted_user(client):
    token = await login_as(client, "u031")
    resp = await client.get("/external/v1/my-access", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 10


async def test_external_access_includes_map_reachable_only_via_one_layer(client):
    root_token = await login_as(client, ROOT)
    await client.put(
        "/grants/layer-roads-bike/user/u016",
        headers=auth_headers(root_token),
        json={"role": "viewer"},
    )

    token = await login_as(client, "u016")
    resp = await client.get(
        "/external/v1/my-access", headers=auth_headers(token), params={"page_size": 50}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "map-city-roads"
    assert body["items"][0]["role"] is None
