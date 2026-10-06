from permissions_server.domain.entities import Grantee, GranteeType, ResourceType, Role, SystemRole

MAP_ID = "map-city-roads"
WORKSPACE_ID = "ws-city"

USER_GRANTEE = Grantee(GranteeType.USER, user_id="u016")


def _find(items, resource_id):
    for item in items:
        if item.id == resource_id:
            return item
        found = _find(item.children, resource_id)
        if found is not None:
            return found
    return None


def _all_ids(items):
    return {item.id for item in items} | {i for item in items for i in _all_ids(item.children)}


async def test_catalog_hides_everything_from_ungranted_user(catalog_service):
    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert page.total == 0
    assert page.items == []


async def test_can_fetch_bubbles_up_from_a_single_accessible_layer(catalog_service, grant_repo):
    """A grant on just one Layer (nothing on the Map itself) still makes the
    Map's can_fetch true — you need to fetch the map to render that layer.
    The Map's OTHER layers, with no role reaching them, stay can_fetch=False."""
    layer_id = "layer-roads-bike"
    await grant_repo.upsert_grant(USER_GRANTEE, layer_id, Role.VIEWER, granted_by="mgr")

    page = await catalog_service.get_catalog("u016", search="City Roads", page=1, page_size=10)
    map_item = page.items[0]
    assert map_item.effective_role is None  # no role at the map's own node
    assert map_item.can_fetch is True  # but it bubbles up from the one granted layer

    # The Map's other layers, with no role reaching them, are pruned.
    assert [c.id for c in map_item.children] == [layer_id]
    assert map_item.children[0].can_fetch is True


async def test_unreachable_siblings_are_hidden_but_path_stays(catalog_service, grant_repo):
    """Only the path down to a reachable resource is shown above it: the
    Workspace appears (no role), sibling branches with nothing reachable
    don't."""
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="mgr")

    page = await catalog_service.get_catalog("u016", search=None, page=1, page_size=10)
    assert page.total == 1
    workspace = page.items[0]
    assert workspace.id == WORKSPACE_ID
    assert workspace.effective_role is None
    assert workspace.can_fetch is True

    visible = _all_ids(page.items)
    assert MAP_ID in visible
    assert "map-zoning" not in visible  # a sibling Map with no grant


async def test_restricted_resource_is_hidden_from_non_whitelisted(
    catalog_service, grant_repo, restriction_repo
):
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.EDITOR, granted_by="mgr")
    await restriction_repo.upsert_restriction(
        Grantee(GranteeType.USER, user_id="u001"), MAP_ID, Role.ADMIN, granted_by="u001"
    )

    page = await catalog_service.get_catalog("u016", search=None, page=1, page_size=10)
    visible = _all_ids(page.items)
    assert WORKSPACE_ID in visible
    assert MAP_ID not in visible


async def test_restriction_whitelist_alone_makes_resource_visible(
    catalog_service, restriction_repo
):
    """A whitelist entry with no grant anywhere is still access — the
    resource (and its path) must show up."""
    await restriction_repo.upsert_restriction(USER_GRANTEE, MAP_ID, Role.VIEWER, granted_by="u001")

    page = await catalog_service.get_catalog("u016", search="City Roads", page=1, page_size=10)
    assert [n.id for n in page.items] == [MAP_ID]
    assert page.items[0].effective_role is Role.VIEWER


async def test_system_role_sees_everything(catalog_service, system_role_repo):
    await system_role_repo.grant_system_role("u031", SystemRole.SUPER_VIEWER, granted_by="test")

    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert page.total == 1
    map_node = _find(page.items, MAP_ID)
    assert map_node.effective_role is Role.VIEWER
    assert len(map_node.children) == 3

    search_page = await catalog_service.get_catalog("u031", search="City Roads", page=1, page_size=10)
    assert [n.id for n in search_page.items] == [MAP_ID]


async def test_pagination_total_counts_only_visible_items(catalog_service, resource_repo, grant_repo):
    for name in ("Alpha", "Beta", "Gamma"):
        ws = await resource_repo.create(type=ResourceType.WORKSPACE, name=name, parent_id=None)
        await grant_repo.upsert_grant(USER_GRANTEE, ws.id, Role.VIEWER, granted_by="mgr")
    await resource_repo.create(type=ResourceType.WORKSPACE, name="Hidden", parent_id=None)

    first = await catalog_service.get_catalog("u016", search=None, page=1, page_size=2)
    second = await catalog_service.get_catalog("u016", search=None, page=2, page_size=2)
    assert first.total == second.total == 3
    assert [n.name for n in first.items] == ["Alpha", "Beta"]
    assert [n.name for n in second.items] == ["Gamma"]


async def test_catalog_search_finds_resource_with_subtree_and_manager_role(
    catalog_service, grant_repo
):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.MANAGER, granted_by="mgr")
    page = await catalog_service.get_catalog("u016", search="City Roads", page=1, page_size=10)

    assert page.total == 1
    map_item = page.items[0]
    assert map_item.id == MAP_ID
    assert map_item.effective_role is Role.MANAGER
    assert map_item.can_manage is True
    assert len(map_item.children) == 3
    assert all(child.effective_role is Role.MANAGER for child in map_item.children)
    assert all(child.can_manage is True for child in map_item.children)


async def test_catalog_editor_role_does_not_allow_manage(catalog_service, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    page = await catalog_service.get_catalog("u016", search="City Roads", page=1, page_size=10)

    map_item = page.items[0]
    assert map_item.effective_role is Role.EDITOR
    assert map_item.can_manage is False


async def test_catalog_search_no_match_returns_empty(catalog_service):
    page = await catalog_service.get_catalog("u001", search="zzz-nomatch", page=1, page_size=10)
    assert page.total == 0
    assert page.items == []


async def test_no_search_pins_callers_personal_workspace_first(
    catalog_service, resource_repo, grant_repo
):
    """Confirmed 2026-07-31: the caller's own personal workspace always shows
    first in the default (no-search) catalog, regardless of alphabetical
    order, so they don't have to hunt for it."""
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE,
        name="Zzz Personal Sandbox",
        parent_id=None,
        owner_id="u016",
    )
    await grant_repo.upsert_grant(USER_GRANTEE, WORKSPACE_ID, Role.VIEWER, granted_by="mgr")

    page = await catalog_service.get_catalog("u016", search=None, page=1, page_size=10)
    assert [n.id for n in page.items] == [personal.id, WORKSPACE_ID]


async def test_own_personal_workspace_shown_even_without_access(catalog_service, resource_repo):
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="My Sandbox", parent_id=None, owner_id="u031"
    )
    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert [n.id for n in page.items] == [personal.id]


async def test_other_users_personal_workspace_is_hidden(catalog_service, resource_repo):
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Someone Else's Sandbox", parent_id=None, owner_id="u999"
    )
    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert personal.id not in {item.id for item in page.items}


async def test_explicit_grant_inside_someone_elses_personal_workspace_still_visible(
    catalog_service, resource_repo, grant_repo
):
    """A non-owner with a real, explicit grant somewhere inside another
    user's personal workspace can still see (and reach) that specific branch
    via search — the hiding rule is "can't reach ANY of it," not "isn't the
    owner." can_fetch bubbling already gives the right answer for free."""
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Shared-Into Sandbox", parent_id=None, owner_id="u999"
    )
    folder = await resource_repo.create(
        type=ResourceType.FOLDER, name="Shared Folder", parent_id=personal.id
    )
    await grant_repo.upsert_grant(USER_GRANTEE, folder.id, Role.EDITOR, granted_by="u999")

    page = await catalog_service.get_catalog("u016", search="Shared Folder", page=1, page_size=10)
    assert len(page.items) == 1
    assert page.items[0].id == folder.id
    assert page.items[0].effective_role is Role.EDITOR


async def test_external_access_filters_out_none_but_totals_all_maps(catalog_service, grant_repo):
    await grant_repo.upsert_grant(USER_GRANTEE, MAP_ID, Role.EDITOR, granted_by="mgr")
    page = await catalog_service.get_external_access("u016", page=1, page_size=50)

    assert page.total == 10  # every Map in the system, not just accessible ones
    assert len(page.items) == 1
    assert page.items[0].id == MAP_ID
    assert page.items[0].role is Role.EDITOR


async def test_external_access_is_empty_for_ungranted_user(catalog_service):
    page = await catalog_service.get_external_access("u031", page=1, page_size=50)
    assert page.items == []
    assert page.total == 10


async def test_external_access_includes_map_reachable_only_via_one_layer(
    catalog_service, grant_repo
):
    """A grant on a single Layer, with no role on the Map itself, still makes
    that Map appear in 'my access' — matches the catalog's can_fetch bubbling."""
    await grant_repo.upsert_grant(USER_GRANTEE, "layer-roads-bike", Role.VIEWER, granted_by="mgr")
    page = await catalog_service.get_external_access("u016", page=1, page_size=50)

    assert len(page.items) == 1
    assert page.items[0].id == MAP_ID
    assert page.items[0].role is None  # no role at the map's own node, just reachable
