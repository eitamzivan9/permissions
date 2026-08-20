from permissions_server.domain.entities import (
    Grantee,
    GranteeType,
    ResourceType,
    Role,
    SystemRole,
)

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


async def test_super_viewer_is_still_admin_on_their_own_personal_workspace(
    access_resolver, resource_repo, grant_repo, system_role_repo
):
    """Confirmed 2026-07-31: SUPER_VIEWER's blanket Viewer-cap is meant to
    apply everywhere ELSE, not shadow an owner's own bootstrap Admin grant on
    their own personal workspace — otherwise being made SUPER_VIEWER would
    perversely demote someone in their own sandbox."""
    workspace = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Their Own Workspace", parent_id=None, owner_id=USER
    )
    await grant_repo.upsert_grant(USER_GRANTEE, workspace.id, Role.ADMIN, granted_by=USER)
    await system_role_repo.grant_system_role(USER, SystemRole.SUPER_VIEWER, granted_by="root")
    assert await access_resolver.effective_role(workspace.id, user_id=USER) is Role.ADMIN
    # Everywhere else, the Viewer cap still applies unchanged.
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


# --- Restrictions: a whitelist gate, layered on top of everything above ---

OTHER_USER_GRANTEE = Grantee(GranteeType.USER, user_id="u099")


async def test_no_restriction_matches_pre_restriction_behavior(access_resolver, grant_repo):
    """Regression guard: with zero Restriction rows anywhere, effective_role
    must behave exactly like before restrictions existed."""
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.EDITOR
    assert await access_resolver.effective_role(LAYER_ID, user_id=USER) is Role.EDITOR


async def test_restriction_at_resource_overrides_a_grant_there(
    access_resolver, grant_repo, restriction_repo
):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")
    await restriction_repo.upsert_restriction(
        USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="admin"
    )
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.VIEWER


async def test_restriction_at_ancestor_unlisted_actor_loses_direct_grant_too(
    access_resolver, grant_repo, restriction_repo
):
    """A restriction 'is greater than any auth' — an actor not on the
    whitelist gets None even though they hold a direct grant on the resource
    itself, since the restriction lives on a nearer-or-equal ancestor."""
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")
    await restriction_repo.upsert_restriction(
        OTHER_USER_GRANTEE, WORKSPACE_ID, Role.VIEWER, granted_by="admin"
    )
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is None


async def test_inherits_from_parent_false_stops_restriction_climb_too(
    access_resolver, grant_repo, restriction_repo, resource_repo
):
    """Baseline: an unlisted actor is denied by a workspace-level
    restriction. Once a barrier sits between the resource and that
    restriction, the restriction can no longer reach down, so the actor's own
    grant resolves normally instead."""
    await restriction_repo.upsert_restriction(
        OTHER_USER_GRANTEE, WORKSPACE_ID, Role.VIEWER, granted_by="admin"
    )
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is None

    await resource_repo.set_inherits_from_parent(FOLDER_ID, False)
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.ADMIN


async def test_restriction_tie_break_is_by_rank_not_recency(access_resolver, restriction_repo):
    """The user explicitly rejected a 'last one set wins' rule — ties among
    restriction entries at one node must break by highest rank, exactly like
    grants. Set the HIGH-rank entry first and the LOW-rank entry last; if
    recency ever won, this would (wrongly) resolve to the low-rank role."""
    team_grantee = Grantee(GranteeType.TEAM, team_id="team-north-ops")
    await restriction_repo.upsert_restriction(
        USER_GRANTEE, MAP_ID, Role.ADMIN, granted_by="admin"
    )
    await restriction_repo.upsert_restriction(
        team_grantee, MAP_ID, Role.VIEWER, granted_by="admin"
    )
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.ADMIN


async def test_super_editor_bypasses_restrictions(
    access_resolver, restriction_repo, system_role_repo
):
    await restriction_repo.upsert_restriction(
        OTHER_USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="admin"
    )
    await system_role_repo.grant_system_role(USER, SystemRole.SUPER_EDITOR, granted_by="root")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.ADMIN


async def test_super_viewer_bypasses_restrictions(
    access_resolver, restriction_repo, system_role_repo
):
    """Confirmed 2026-07-31: both system-wide roles are "greater than any
    permission" — SUPER_VIEWER bypasses a restriction gate the same way
    SUPER_EDITOR does, just resolving to Viewer instead of Admin."""
    await restriction_repo.upsert_restriction(
        OTHER_USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="admin"
    )
    await system_role_repo.grant_system_role(USER, SystemRole.SUPER_VIEWER, granted_by="root")
    assert await access_resolver.effective_role(MAP_ID, user_id=USER) is Role.VIEWER


# --- nearest_admins: "who do I ask" for a caller with no access ---


async def test_nearest_admins_empty_with_no_grants_anywhere(access_resolver):
    assert await access_resolver.nearest_admins(MAP_ID) == []


async def test_nearest_admins_returns_admin_grantees_at_nearest_node(access_resolver, grant_repo):
    other_admin = Grantee(GranteeType.USER, user_id="u099")
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")
    await grant_repo.upsert_grant(other_admin, MAP_ID, Role.ADMIN, granted_by="mgr")
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id="u050"), MAP_ID, Role.EDITOR, granted_by="mgr"
    )
    admins = await access_resolver.nearest_admins(MAP_ID)
    assert set(admins) == {USER_GRANTEE, other_admin}


async def test_nearest_admins_excludes_non_admin_grantees_at_the_node(access_resolver, grant_repo):
    """A node can have grants without anyone there being Admin — the
    resource genuinely has no admin via inheritance in that case (a further
    ancestor's Admin grant is overridden, same as effective_role would
    resolve for that ancestor's grantee)."""
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    assert await access_resolver.nearest_admins(MAP_ID) == []


async def test_nearest_admins_climbs_to_nearest_ancestor_with_any_grant(access_resolver, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.ADMIN, granted_by="mgr")
    assert await access_resolver.nearest_admins(LAYER_ID) == [USER_GRANTEE]


async def test_nearest_admins_stops_at_inherits_from_parent_false(
    access_resolver, grant_repo, resource_repo
):
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.ADMIN, granted_by="mgr")
    await resource_repo.set_inherits_from_parent(FOLDER_ID, False)
    assert await access_resolver.nearest_admins(MAP_ID) == []


async def test_nearest_restriction_computes_its_own_path_when_not_given(
    access_resolver, restriction_repo
):
    """Direct callers (unlike effective_role/nearest_admins, which always
    pass a precomputed path) rely on nearest_restriction fetching its own
    path_to_root."""
    await restriction_repo.upsert_restriction(USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="admin")
    result = await access_resolver.nearest_restriction(MAP_ID)
    assert result is not None
    origin_id, entries = result
    assert origin_id == MAP_ID
    assert entries[0].grantee == USER_GRANTEE


async def test_nearest_restriction_none_for_nonexistent_resource(access_resolver):
    assert await access_resolver.nearest_restriction("does-not-exist") is None


async def test_path_to_root_terminates_on_a_corrupted_cyclic_parent_chain(resource_repo):
    """Not reachable through the normal API (move() rejects moving a
    resource into its own subtree) — this guards the repository itself
    against hanging forever if parent_id data is ever corrupted directly,
    same defensive style as MockOrgHierarchy's visited-set guard."""
    a = await resource_repo.create(type=ResourceType.WORKSPACE, name="A", parent_id=None)
    b = await resource_repo.create(type=ResourceType.FOLDER, name="B", parent_id=a.id)
    # Force a cycle: b's own child ends up pointing back at a's OWN parent_id,
    # by making a directly point at b (bypassing move()'s cycle check).
    resource_repo._by_id[a.id] = type(a)(
        id=a.id, type=a.type, name=a.name, parent_id=b.id, owner_id=a.owner_id
    )
    path = await resource_repo.path_to_root(b.id)
    assert len(path) <= 2  # terminates instead of looping forever


async def test_nearest_admins_uses_restriction_whitelist_when_restricted(
    access_resolver, restriction_repo
):
    """When a restriction gates the resource, 'who do I ask' must reflect
    who the restriction actually lets through as Admin — not grants, which
    the restriction fully overrides."""
    admin_entry = Grantee(GranteeType.USER, user_id="u070")
    await restriction_repo.upsert_restriction(admin_entry, MAP_ID, Role.ADMIN, granted_by="admin")
    await restriction_repo.upsert_restriction(
        OTHER_USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="admin"
    )
    assert await access_resolver.nearest_admins(MAP_ID) == [admin_entry]
