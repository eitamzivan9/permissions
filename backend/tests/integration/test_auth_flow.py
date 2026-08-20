from tests.integration.conftest import auth_headers, login_as


async def test_login_then_me_round_trip(client):
    token = await login_as(client, "u001")
    resp = await client.get("/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "u001"
    assert body["name"] == "Dana Whitfield"


async def test_login_unknown_user_is_404(client):
    resp = await client.post("/auth/login", json={"user_id": "does-not-exist"})
    assert resp.status_code == 404


async def test_protected_route_without_token_is_401(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_protected_route_with_garbage_token_is_401(client):
    resp = await client.get("/auth/me", headers=auth_headers("not-a-real-jwt"))
    assert resp.status_code == 401


async def test_list_mock_users_returns_the_dev_login_picker_fixture(client):
    resp = await client.get("/auth/mock-users")
    assert resp.status_code == 200
    users = resp.json()
    assert any(u["id"] == "u001" and u["name"] == "Dana Whitfield" for u in users)
