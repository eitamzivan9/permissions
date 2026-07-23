from tests.integration.conftest import auth_headers, login_as

ROOT = "u001"
MAP_ID = "map-zoning"
VIEWER_USER = "u016"


async def test_create_team_add_member_then_grant_reaches_member_via_team(client):
    root_token = await login_as(client, ROOT)
    headers = auth_headers(root_token)

    create_resp = await client.post("/teams", headers=headers, json={"name": "Zoning Reviewers"})
    assert create_resp.status_code == 201
    team_id = create_resp.json()["id"]

    add_resp = await client.post(f"/teams/{team_id}/members/{VIEWER_USER}", headers=headers)
    assert add_resp.status_code == 204

    members_resp = await client.get(f"/teams/{team_id}/members", headers=headers)
    assert members_resp.status_code == 200
    assert {m["user_id"] for m in members_resp.json()} == {VIEWER_USER}

    grant_resp = await client.put(
        f"/grants/{MAP_ID}/team/{team_id}", headers=headers, json={"role": "viewer"}
    )
    assert grant_resp.status_code == 200

    member_token = await login_as(client, VIEWER_USER)
    catalog = await client.get(
        "/catalog", headers=auth_headers(member_token), params={"q": "Zoning Districts"}
    )
    assert catalog.json()["items"][0]["effective_role"] == "viewer"


async def test_my_access_and_check_access_endpoints(client):
    root_token = await login_as(client, ROOT)
    root_headers = auth_headers(root_token)
    await client.put(
        f"/grants/{MAP_ID}/user/{VIEWER_USER}", headers=root_headers, json={"role": "viewer"}
    )

    viewer_token = await login_as(client, VIEWER_USER)
    my_access_resp = await client.get(
        f"/access/my-access/{MAP_ID}", headers=auth_headers(viewer_token)
    )
    assert my_access_resp.status_code == 200
    sources = my_access_resp.json()
    assert any(s["role"] == "viewer" and s["is_effective"] for s in sources)

    # root is Admin (bootstrap seed) everywhere, so it may inspect anyone's access
    check_resp = await client.get(
        f"/access/check-access/{MAP_ID}/{VIEWER_USER}", headers=root_headers
    )
    assert check_resp.status_code == 200
    assert any(s["role"] == "viewer" for s in check_resp.json())

    # the viewer itself has no Manager+ role, so it may not inspect others
    forbidden_resp = await client.get(
        f"/access/check-access/{MAP_ID}/{ROOT}", headers=auth_headers(viewer_token)
    )
    assert forbidden_resp.status_code == 403


async def test_audit_endpoint_records_grant_and_revoke(client):
    root_token = await login_as(client, ROOT)
    headers = auth_headers(root_token)
    await client.put(f"/grants/{MAP_ID}/user/{VIEWER_USER}", headers=headers, json={"role": "viewer"})
    await client.delete(f"/grants/{MAP_ID}/user/{VIEWER_USER}", headers=headers)

    resp = await client.get(f"/audit/resource/{MAP_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    actions = [item["action"] for item in body["items"]]
    assert actions == ["revoke", "grant"]  # newest first
