"""Verifies the visited-set guards in MockOrgHierarchy actually stop traversal
on cyclic manager_id data instead of hanging — using a deliberately corrupted
fixture (the real mock_users.json has no cycles, so this must be synthetic)."""

import pytest

import permissions_server.infrastructure.auth.mock_org_hierarchy as org_module
from permissions_server.infrastructure.auth.mock_org_hierarchy import MockOrgHierarchy

# a -> b -> c -> a is a cycle; d reports (validly) into the cycle at 'a'
CYCLIC_RECORDS = [
    {"id": "a", "name": "A", "email": "a@x", "manager_id": "b"},
    {"id": "b", "name": "B", "email": "b@x", "manager_id": "c"},
    {"id": "c", "name": "C", "email": "c@x", "manager_id": "a"},
    {"id": "d", "name": "D", "email": "d@x", "manager_id": "a"},
]


@pytest.fixture(autouse=True)
def patch_fixture(monkeypatch):
    monkeypatch.setattr(org_module, "load_mock_users", lambda: CYCLIC_RECORDS)


async def test_is_manager_of_terminates_instead_of_looping_forever():
    org = MockOrgHierarchy()
    # walking up from 'a' revisits a->b->c->a indefinitely without the guard
    assert await org.is_manager_of("nobody-in-the-chain", "a") is False


async def test_is_manager_of_still_finds_real_relationships():
    org = MockOrgHierarchy()
    assert await org.is_manager_of("a", "d") is True


async def test_subordinates_of_terminates_and_finds_real_subordinates():
    org = MockOrgHierarchy()
    result = await org.subordinates_of("a")
    assert "d" in result
    assert "b" in result
    assert "c" in result
