from permissions_server.domain.entities import Grantee, GranteeType, Role, SystemRole

MAP_ID = "map-city-roads"
LAYER_ID = "layer-roads-bike"
OTHER_LAYER_ID = "layer-roads-highways"
FOLDER_ID = "f-infrastructure"
WORKSPACE_ID = "ws-city"
USER = "u016"

USER_GRANTEE = Grantee(GranteeType.USER, user_id=USER)


async def test_no_grants_means_none(access_resolver):
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is None
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is None


async def test_layer_inherits_map_default(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.EDITOR
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.EDITOR
    assert await access_resolver.effective_role(OTHER_LAYER_ID, user_id=USER) is Role.EDITOR


async def test_layer_override_wins_over_map_default(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    await grant_repo.upsert_grant(USER_GRANTEE, LAYER_ID, Role.VIEWER, granted_by="mgr")
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.VIEWER
    assert await access_resolver.effective_role(OTHER_LAYER_ID, user_id=USER) is Role.EDITOR
    # the map-level grant itself is untouched
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.EDITOR


async def test_nearest_ancestor_wins_over_farther_grandparent(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.ADMIN, granted_by="mgr")
    await grant_repo.upsert_grant(USER_GRANTEE, FOLDER_ID, Role.EDITOR, granted_by="mgr")
    # the closer Folder grant overrides the farther Workspace grant everywhere below it
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.EDITOR
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.EDITOR


async def test_deleting_layer_override_reverts_to_map_default(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    await grant_repo.upsert_grant(USER_GRANTEE, LAYER_ID, Role.VIEWER, granted_by="mgr")
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.VIEWER

    await grant_repo.delete_grant(USER_GRANTEE, LAYER_ID)
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.EDITOR


async def test_team_grant_used_when_no_direct_grant(access_resolver, grant_repo):
    team_grantee = Grantee(GranteeType.TEAM, team_id="team-north-ops")
    await grant_repo.upsert_grant(team_grantee, MAP_ID, Role.EDITOR, granted_by="mgr")
    # u016 is a member of team-north-ops per seed_data.TEAM_MEMBERSHIPS
    assert await access_resolver.effective_role(MAP_ID, user_id="u016") is Role.EDITOR


async def test_highest_rank_wins_between_direct_and_team_grant(access_resolver, grant_repo):
    team_grantee = Grantee(GranteeType.TEAM, team_id="team-north-ops")
    await grant_repo.upsert_grant(team_grantee, MAP_ID, Role.VIEWER, granted_by="mgr")
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id="u016"), MAP_ID, Role.ADMIN, granted_by="mgr"
    )
    assert await access_resolver.effective_role(MAP_ID, user_id="u016") is Role.ADMIN


async def test_super_editor_bypasses_everything(access_resolver, system_role_repo):
    await system_role_repo.grant_system_role(USER, SystemRole.SUPER_EDITOR, granted_by="root")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.ADMIN
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.ADMIN


async def test_super_viewer_bypasses_everything_read_only(access_resolver, system_role_repo):
    await system_role_repo.grant_system_role(USER, SystemRole.SUPER_VIEWER, granted_by="root")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.VIEWER


async def test_snapshot_matches_individual_lookups(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="mgr")
    snapshot = await access_resolver.snapshot_for_user(USER)
    assert await access_resolver.effective_role(MAP_ID, snapshot=snapshot) is Role.VIEWER
    assert await access_resolver.effective_role(LAYER_ID, snapshot=snapshot) is Role.VIEWER


async def test_inherits_from_parent_false_walls_off_the_workspace_grant(
    access_resolver, grant_repo, resource_repo
):
    """A workspace-wide grant normally reaches every descendant. Flipping
    inherits_from_parent=False on the Folder cuts that climb at the Folder
    itself — the Folder and everything below it get no role from the
    Workspace anymore, with no grant enumerated for anyone."""
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.EDITOR, granted_by="mgr")
    assert await access_resolver.effective_role(FOLDER_ID, user_id=USER) is Role.EDITOR
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.EDITOR

    await resource_repo.set_inherits_from_parent(FOLDER_ID, False)
    assert await access_resolver.effective_role(FOLDER_ID, user_id=USER) is None
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is None
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is None


async def test_inherits_from_parent_false_still_honors_its_own_grant(
    access_resolver, grant_repo, resource_repo
):
    """The barrier only blocks what would have come from ABOVE it — a grant
    placed directly on the barrier node (or below) still applies normally."""
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.EDITOR, granted_by="mgr")
    await resource_repo.set_inherits_from_parent(FOLDER_ID, False)
    await grant_repo.upsert_grant(USER_GRANTEE, FOLDER_ID, Role.VIEWER, granted_by="mgr")

    assert await access_resolver.effective_role(FOLDER_ID, user_id=USER) is Role.VIEWER
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.VIEWER
