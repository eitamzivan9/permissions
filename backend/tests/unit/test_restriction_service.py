import pytest

from permissions_server.domain.entities import (
    AuditAction,
    AuthenticatedUser,
    Grantee,
    GranteeType,
    ResourceType,
    Role,
)
from permissions_server.domain.errors import ConflictError

# Real mock-org-chart ids (see mock_users.json): u002 manages u004/u005
# directly and u016 transitively (u002 -> u004 -> u008 -> u016) — needed
# because can_set_restriction's org-chart check is real, not stubbable.
ADMIN = AuthenticatedUser(id="u002", name="Marcus Ilic", email="marcus.ilic@geoteam.example")
OTHER_ADMIN = AuthenticatedUser(id="u001", name="Dana Whitfield", email="dana.whitfield@geoteam.example")
OTHER_USER_GRANTEE = Grantee(GranteeType.USER, user_id="u016")


@pytest.fixture
async def resource(resource_repo):
    return await resource_repo.create(type=ResourceType.MAP, name="map", parent_id=None)


async def _make_admin(grant_repo, actor, resource_id):
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id=actor.id), resource_id, Role.ADMIN, granted_by="seed"
    )


async def test_first_restriction_auto_whitelists_the_acting_admin(
    restriction_service, restriction_repo, grant_repo, resource
):
    await _make_admin(grant_repo, ADMIN, resource.id)

    await restriction_service.set_restriction(
        ADMIN, OTHER_USER_GRANTEE, resource.id, Role.VIEWER
    )

    entries = await restriction_repo.list_restrictions_for_resource(resource.id)
    grantees = {e.grantee for e in entries}
    assert OTHER_USER_GRANTEE in grantees
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    assert admin_grantee in grantees
    admin_entry = next(e for e in entries if e.grantee == admin_grantee)
    assert admin_entry.role is Role.ADMIN


async def test_first_restriction_does_not_duplicate_when_actor_restricts_self(
    restriction_service, restriction_repo, grant_repo, resource
):
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)

    await restriction_service.set_restriction(ADMIN, admin_grantee, resource.id, Role.ADMIN)

    entries = await restriction_repo.list_restrictions_for_resource(resource.id)
    assert len(entries) == 1
    assert entries[0].grantee == admin_grantee


async def test_second_restriction_does_not_auto_whitelist_again(
    restriction_service, restriction_repo, grant_repo, resource, audit_log_repo
):
    """Row-count can't distinguish 'added once' from 'upserted twice' (same
    key just overwrites), so this checks the audit trail instead: the
    auto-whitelist RESTRICT record for the actor must appear exactly once,
    from the FIRST set_restriction call only."""
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    another_grantee = Grantee(GranteeType.USER, user_id="u005")

    await restriction_service.set_restriction(
        ADMIN, OTHER_USER_GRANTEE, resource.id, Role.VIEWER
    )
    await restriction_service.set_restriction(ADMIN, another_grantee, resource.id, Role.VIEWER)

    history = await audit_log_repo.list_for_resource(resource.id, page=1, page_size=20)
    admin_restrict_entries = [
        e
        for e in history.items
        if e.grantee == admin_grantee and e.action is AuditAction.RESTRICT
    ]
    assert len(admin_restrict_entries) == 1


async def test_revoke_last_admin_restriction_is_conflict_when_other_entries_remain(
    restriction_service, restriction_repo, grant_repo, resource
):
    """The orphan case the guard exists for: removing the last Admin entry
    while the resource STAYS gated (another, non-admin entry remains)."""
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    await restriction_service.set_restriction(
        ADMIN, OTHER_USER_GRANTEE, resource.id, Role.VIEWER
    )  # auto-whitelists ADMIN as the only Admin-role entry

    with pytest.raises(ConflictError):
        await restriction_service.revoke_restriction(ADMIN, admin_grantee, resource.id)

    assert await restriction_repo.get_restriction(admin_grantee, resource.id) is not None


async def test_revoke_the_only_remaining_restriction_is_allowed_even_if_admin_role(
    restriction_service, restriction_repo, grant_repo, resource
):
    """Removing the LAST restriction row overall is always allowed, even if
    it's Admin-role — that's a full unrestrict (falls back to ordinary
    grants), not an orphan, and 'Clear all' must be able to reach zero."""
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    await restriction_service.set_restriction(ADMIN, admin_grantee, resource.id, Role.ADMIN)

    await restriction_service.revoke_restriction(ADMIN, admin_grantee, resource.id)

    assert await restriction_repo.list_restrictions_for_resource(resource.id) == []


async def test_revoke_admin_restriction_succeeds_when_another_admin_remains(
    restriction_service, restriction_repo, grant_repo, resource
):
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    other_admin_grantee = Grantee(GranteeType.USER, user_id=OTHER_ADMIN.id)

    await restriction_service.set_restriction(ADMIN, admin_grantee, resource.id, Role.ADMIN)
    await restriction_repo.upsert_restriction(
        other_admin_grantee, resource.id, Role.ADMIN, granted_by=ADMIN.id
    )

    await restriction_service.revoke_restriction(ADMIN, admin_grantee, resource.id)

    assert await restriction_repo.get_restriction(admin_grantee, resource.id) is None
    assert await restriction_repo.get_restriction(other_admin_grantee, resource.id) is not None


async def test_revoke_non_admin_restriction_never_blocked_by_last_admin_guard(
    restriction_service, restriction_repo, grant_repo, resource
):
    await _make_admin(grant_repo, ADMIN, resource.id)
    admin_grantee = Grantee(GranteeType.USER, user_id=ADMIN.id)
    await restriction_service.set_restriction(
        ADMIN, OTHER_USER_GRANTEE, resource.id, Role.VIEWER
    )
    # OTHER_USER_GRANTEE holds Viewer, ADMIN (auto-whitelisted) is the only
    # Admin entry — revoking the Viewer entry must never be blocked, since
    # the guard only cares about Admin-role entries.
    await restriction_service.revoke_restriction(ADMIN, OTHER_USER_GRANTEE, resource.id)

    assert await restriction_repo.get_restriction(OTHER_USER_GRANTEE, resource.id) is None
    assert await restriction_repo.get_restriction(admin_grantee, resource.id) is not None
