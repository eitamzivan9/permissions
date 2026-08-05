import pytest

from permissions_server.domain.entities import (
    AuditAction,
    AuthenticatedUser,
    Grantee,
    GranteeType,
    ResourceType,
    Role,
    SystemRole,
)
from permissions_server.domain.errors import ForbiddenError

MAP_ID = "map-city-roads"
LAYER_ID = "layer-roads-bike"

# u002 (VP) -> u004 (director) -> u008 (manager) -> u016 (IC): 3 levels down, transitive
ACTOR = AuthenticatedUser(id="u002", name="Marcus Ilic", email="marcus.ilic@geoteam.example")
SUBORDINATE_ID = "u016"
# u024 sits under the OTHER VP's branch (u003 -> u006 -> u012 -> u024) — not actor's subordinate
NOT_SUBORDINATE_ID = "u024"

SUBORDINATE_GRANTEE = Grantee(GranteeType.USER, user_id=SUBORDINATE_ID)
NOT_SUBORDINATE_GRANTEE = Grantee(GranteeType.USER, user_id=NOT_SUBORDINATE_ID)
TEAM_GRANTEE = Grantee(GranteeType.TEAM, team_id="team-gis-analysts")


async def _give_actor_role(grant_repo, role):
    actor_grantee = Grantee(GranteeType.USER, user_id=ACTOR.id)
    await grant_repo.upsert_grant(actor_grantee, MAP_ID, role, granted_by="seed")


async def test_can_manage_true_when_manager_and_transitive_subordinate(
    permission_grant_service, grant_repo
):
    await _give_actor_role(grant_repo, Role.MANAGER)
    assert (
        await permission_grant_service.can_manage(ACTOR, SUBORDINATE_GRANTEE, MAP_ID, Role.EDITOR)
        is True
    )


async def test_can_manage_false_when_manager_but_not_subordinate(
    permission_grant_service, grant_repo
):
    await _give_actor_role(grant_repo, Role.MANAGER)
    assert (
        await permission_grant_service.can_manage(
            ACTOR, NOT_SUBORDINATE_GRANTEE, MAP_ID, Role.EDITOR
        )
        is False
    )


async def test_can_manage_false_when_subordinate_but_only_editor_role(
    permission_grant_service, grant_repo
):
    await _give_actor_role(grant_repo, Role.EDITOR)
    assert (
        await permission_grant_service.can_manage(ACTOR, SUBORDINATE_GRANTEE, MAP_ID, Role.VIEWER)
        is False
    )


async def test_can_manage_false_when_manager_tries_to_grant_manager(
    permission_grant_service, grant_repo
):
    await _give_actor_role(grant_repo, Role.MANAGER)
    assert (
        await permission_grant_service.can_manage(ACTOR, SUBORDINATE_GRANTEE, MAP_ID, Role.MANAGER)
        is False
    )


async def test_can_manage_true_when_admin_grants_manager(permission_grant_service, grant_repo):
    await _give_actor_role(grant_repo, Role.ADMIN)
    assert (
        await permission_grant_service.can_manage(ACTOR, SUBORDINATE_GRANTEE, MAP_ID, Role.MANAGER)
        is True
    )


async def test_can_manage_via_inherited_role_on_layer_target(
    permission_grant_service, grant_repo
):
    """A manager's role on a layer target can come from the map-level
    default, not just a direct layer-scope grant — can_manage must check via
    AccessResolver's inheritance climb."""
    await _give_actor_role(grant_repo, Role.MANAGER)
    assert (
        await permission_grant_service.can_manage(
            ACTOR, SUBORDINATE_GRANTEE, LAYER_ID, Role.EDITOR
        )
        is True
    )


async def test_can_manage_true_for_team_grantee_regardless_of_org_chart(
    permission_grant_service, grant_repo
):
    """Team grantees skip the org-chart check entirely — only role rank
    matters, matching the docx/repo (no team is anyone's org subordinate)."""
    await _give_actor_role(grant_repo, Role.MANAGER)
    assert (
        await permission_grant_service.can_manage(ACTOR, TEAM_GRANTEE, MAP_ID, Role.EDITOR) is True
    )


async def test_grant_succeeds_when_authorized_and_records_audit(
    permission_grant_service, grant_repo, audit_log_repo
):
    await _give_actor_role(grant_repo, Role.MANAGER)
    result = await permission_grant_service.grant(
        ACTOR, SUBORDINATE_GRANTEE, LAYER_ID, Role.VIEWER
    )
    assert result.role is Role.VIEWER
    assert result.granted_by == ACTOR.id

    stored = await grant_repo.get_grant(SUBORDINATE_GRANTEE, LAYER_ID)
    assert stored is not None and stored.role is Role.VIEWER

    history = await audit_log_repo.list_for_resource(LAYER_ID, page=1, page_size=10)
    assert history.total == 1
    assert history.items[0].actor_id == ACTOR.id


async def test_regrant_with_a_different_role_logs_role_change_not_grant(
    permission_grant_service, grant_repo, audit_log_repo
):
    await _give_actor_role(grant_repo, Role.MANAGER)
    await permission_grant_service.grant(ACTOR, SUBORDINATE_GRANTEE, LAYER_ID, Role.VIEWER)
    await permission_grant_service.grant(ACTOR, SUBORDINATE_GRANTEE, LAYER_ID, Role.EDITOR)

    stored = await grant_repo.get_grant(SUBORDINATE_GRANTEE, LAYER_ID)
    assert stored is not None and stored.role is Role.EDITOR

    history = await audit_log_repo.list_for_resource(LAYER_ID, page=1, page_size=10)
    assert history.total == 2
    # newest first
    assert history.items[0].action is AuditAction.ROLE_CHANGE
    assert history.items[0].role is Role.EDITOR
    assert history.items[1].action is AuditAction.GRANT
    assert history.items[1].role is Role.VIEWER


async def test_grant_raises_forbidden_when_unauthorized_and_writes_nothing(
    permission_grant_service, grant_repo
):
    with pytest.raises(ForbiddenError):
        await permission_grant_service.grant(ACTOR, SUBORDINATE_GRANTEE, MAP_ID, Role.EDITOR)
    assert await grant_repo.get_grant(SUBORDINATE_GRANTEE, MAP_ID) is None


async def test_revoke_raises_forbidden_when_unauthorized_and_leaves_grant_untouched(
    permission_grant_service, grant_repo
):
    await grant_repo.upsert_grant(
        SUBORDINATE_GRANTEE, LAYER_ID, Role.VIEWER, granted_by="someone-else"
    )
    with pytest.raises(ForbiddenError):
        await permission_grant_service.revoke(ACTOR, SUBORDINATE_GRANTEE, LAYER_ID)

    still_there = await grant_repo.get_grant(SUBORDINATE_GRANTEE, LAYER_ID)
    assert still_there is not None and still_there.role is Role.VIEWER


async def test_revoke_succeeds_when_authorized(permission_grant_service, grant_repo):
    await _give_actor_role(grant_repo, Role.MANAGER)
    await grant_repo.upsert_grant(
        SUBORDINATE_GRANTEE, LAYER_ID, Role.VIEWER, granted_by="someone-else"
    )

    await permission_grant_service.revoke(ACTOR, SUBORDINATE_GRANTEE, LAYER_ID)
    assert await grant_repo.get_grant(SUBORDINATE_GRANTEE, LAYER_ID) is None


async def test_revoke_is_noop_when_no_existing_grant(permission_grant_service, grant_repo):
    await permission_grant_service.revoke(ACTOR, SUBORDINATE_GRANTEE, LAYER_ID)  # no raise


async def test_list_manageable_users_returns_only_transitive_subordinates(
    permission_grant_service,
):
    users = await permission_grant_service.list_manageable_users(ACTOR)
    ids = {u.id for u in users}
    assert SUBORDINATE_ID in ids
    assert NOT_SUBORDINATE_ID not in ids
    assert ACTOR.id not in ids


async def test_can_manage_true_for_non_subordinate_inside_own_personal_workspace(
    permission_grant_service, grant_repo, resource_repo
):
    """A personal workspace's owner has authority over its whole subtree
    regardless of the org chart — it's their own sandbox, not something
    they manage by reporting-line authority (NOT_SUBORDINATE_ID is
    deliberately not ACTOR's subordinate elsewhere in this file)."""
    workspace = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Actor's Workspace", parent_id=None, owner_id=ACTOR.id
    )
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id=ACTOR.id), workspace.id, Role.ADMIN, granted_by=ACTOR.id
    )
    assert (
        await permission_grant_service.can_manage(
            ACTOR, NOT_SUBORDINATE_GRANTEE, workspace.id, Role.EDITOR
        )
        is True
    )


async def test_can_manage_false_for_non_subordinate_inside_someone_elses_personal_workspace(
    permission_grant_service, grant_repo, resource_repo
):
    """The bypass is scoped to the OWNER's own workspace — an Admin grant
    someone else handed out inside a different user's personal workspace
    still goes through the ordinary org-chart check."""
    workspace = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Someone Else's Workspace", parent_id=None, owner_id="u999"
    )
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id=ACTOR.id), workspace.id, Role.ADMIN, granted_by="u999"
    )
    assert (
        await permission_grant_service.can_manage(
            ACTOR, NOT_SUBORDINATE_GRANTEE, workspace.id, Role.EDITOR
        )
        is False
    )


async def test_list_manageable_users_returns_everyone_inside_own_personal_workspace(
    permission_grant_service, grant_repo, resource_repo
):
    workspace = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Actor's Workspace", parent_id=None, owner_id=ACTOR.id
    )
    users = await permission_grant_service.list_manageable_users(ACTOR, resource_id=workspace.id)
    ids = {u.id for u in users}
    assert SUBORDINATE_ID in ids
    assert NOT_SUBORDINATE_ID in ids  # the whole point of the bypass


async def test_list_manageable_users_ignores_resource_id_outside_own_personal_workspace(
    permission_grant_service,
):
    users = await permission_grant_service.list_manageable_users(ACTOR, resource_id=MAP_ID)
    ids = {u.id for u in users}
    assert NOT_SUBORDINATE_ID not in ids


async def test_list_manageable_users_returns_everyone_for_super_editor(
    permission_grant_service, system_role_repo
):
    """Found via manual UI testing 2026-07-31: can_manage already lets a
    SUPER_EDITOR grant to anyone (bypasses the org-chart check entirely), but
    this listing didn't know that — the picker showed "no one available" even
    though the grant itself would have succeeded. NOT_SUBORDINATE_ID (not
    ACTOR's subordinate anywhere in this file) proves the bypass, same as the
    personal-workspace case above."""
    await system_role_repo.grant_system_role(ACTOR.id, SystemRole.SUPER_EDITOR, granted_by="root")
    users = await permission_grant_service.list_manageable_users(ACTOR, resource_id=MAP_ID)
    ids = {u.id for u in users}
    assert NOT_SUBORDINATE_ID in ids
