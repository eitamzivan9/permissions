"""Exercises SqlAlchemySystemRoleRepository against real Postgres, including
the composite (user_id, role) primary key that lets a user hold both
SUPER_EDITOR and SUPER_VIEWER as independent rows."""

from __future__ import annotations

from permissions_server.domain.entities import SystemRole


async def test_grant_then_list_system_roles(system_role_repo):
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="u000")
    assert await system_role_repo.list_system_roles("u001") == frozenset({SystemRole.SUPER_EDITOR})


async def test_grant_is_idempotent(system_role_repo):
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="u000")
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="u000")
    assert await system_role_repo.list_system_roles("u001") == frozenset({SystemRole.SUPER_EDITOR})


async def test_user_can_hold_both_system_roles_independently(system_role_repo):
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="u000")
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_VIEWER, granted_by="u000")
    assert await system_role_repo.list_system_roles("u001") == frozenset(
        {SystemRole.SUPER_EDITOR, SystemRole.SUPER_VIEWER}
    )


async def test_revoke_system_role(system_role_repo):
    await system_role_repo.grant_system_role("u001", SystemRole.SUPER_EDITOR, granted_by="u000")
    await system_role_repo.revoke_system_role("u001", SystemRole.SUPER_EDITOR)
    assert await system_role_repo.list_system_roles("u001") == frozenset()
    # revoking again is a no-op, not an error
    await system_role_repo.revoke_system_role("u001", SystemRole.SUPER_EDITOR)
