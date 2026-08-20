"""Direct tests for in-memory repository methods that no application service
currently exercises on its hot path (kept for port parity/future tooling —
see their docstrings) but must still behave correctly on their own."""

from permissions_server.domain.entities import Grantee, GranteeType, Role, SystemRole
from permissions_server.infrastructure.memory.in_memory_restriction_repository import (
    InMemoryRestrictionRepository,
)
from permissions_server.infrastructure.memory.in_memory_system_role_repository import (
    InMemorySystemRoleRepository,
)

USER_A = Grantee(GranteeType.USER, user_id="u001")
USER_B = Grantee(GranteeType.USER, user_id="u002")
TEAM_A = Grantee(GranteeType.TEAM, team_id="team-a")


async def test_list_restrictions_for_grantees_filters_to_the_given_grantees():
    repo = InMemoryRestrictionRepository()
    await repo.upsert_restriction(USER_A, "res-1", Role.VIEWER, granted_by="admin")
    await repo.upsert_restriction(USER_B, "res-2", Role.VIEWER, granted_by="admin")
    await repo.upsert_restriction(TEAM_A, "res-3", Role.EDITOR, granted_by="admin")

    result = await repo.list_restrictions_for_grantees([USER_A, TEAM_A])
    resource_ids = {r.resource_id for r in result}
    assert resource_ids == {"res-1", "res-3"}


async def test_list_restrictions_for_grantees_empty_when_none_match():
    repo = InMemoryRestrictionRepository()
    await repo.upsert_restriction(USER_B, "res-2", Role.VIEWER, granted_by="admin")
    assert await repo.list_restrictions_for_grantees([USER_A]) == []


async def test_revoke_system_role_removes_only_the_named_role():
    repo = InMemorySystemRoleRepository()
    await repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="root")
    await repo.grant_system_role("u001", SystemRole.SUPER_VIEWER, granted_by="root")

    await repo.revoke_system_role("u001", SystemRole.SUPER_EDITOR)

    remaining = await repo.list_system_roles("u001")
    assert remaining == frozenset({SystemRole.SUPER_VIEWER})


async def test_revoke_system_role_is_a_no_op_for_a_user_with_no_roles():
    repo = InMemorySystemRoleRepository()
    # Must not raise even though "u099" has never been granted anything.
    await repo.revoke_system_role("u099", SystemRole.SUPER_EDITOR)
    assert await repo.list_system_roles("u099") == frozenset()
