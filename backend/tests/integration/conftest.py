import httpx
import pytest_asyncio

from permissions_server.main import create_app


@pytest_asyncio.fixture
async def client():
    """A fresh app + in-memory state per test, talked to over real HTTP
    semantics (headers, status codes, JSON) via ASGI — not by calling Python
    functions directly. Manually drives the lifespan context since
    httpx.ASGITransport doesn't run FastAPI's startup/shutdown on its own."""
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            # No HTTP endpoint grants system roles (same as production) — tests
            # that need a SUPER_EDITOR/SUPER_VIEWER seed it directly here, the
            # same way unit tests seed it directly on system_role_repo.
            ac.app_state = app.state  # type: ignore[attr-defined]
            yield ac


async def login_as(client: httpx.AsyncClient, user_id: str) -> str:
    resp = await client.post("/auth/login", json={"user_id": user_id})
    resp.raise_for_status()
    return resp.json()["token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
