from permissions_server.domain.entities import Grantee, GranteeType, ResourceType, Role

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


async def test_catalog_no_search_returns_full_workspace_tree_annotated_none(catalog_service):
    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)

    assert page.total == 1  # one seeded Workspace
    workspace = page.items[0]
    assert workspace.id == WORKSPACE_ID
    assert workspace.effective_role is None
    assert workspace.can_manage is False
    assert workspace.can_fetch is False

    map_node = _find(page.items, MAP_ID)
    assert map_node is not None
    assert map_node.effective_role is None
    assert map_node.can_fetch is False
    assert len(map_node.children) == 3  # highways, local, bike layers
    assert all(child.effective_role is None for child in map_node.children)


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

    granted_layer = next(c for c in map_item.children if c.id == layer_id)
    assert granted_layer.can_fetch is True
    other_layers = [c for c in map_item.children if c.id != layer_id]
    assert all(c.can_fetch is False for c in other_layers)


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


async def test_no_search_pins_callers_personal_workspace_first(catalog_service, resource_repo):
    """Confirmed 2026-07-31: the caller's own personal workspace always shows
    first in the default (no-search) catalog, regardless of alphabetical
    order, so they don't have to hunt for it."""
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE,
        name="Zzz Personal Sandbox",
        parent_id=None,
        owner_id="u999",
    )

    page = await catalog_service.get_catalog("u999", search=None, page=1, page_size=10)
    assert page.items[0].id == personal.id

    # A different caller with no access to u999's personal workspace doesn't
    # see it at all (see test_other_users_personal_workspace_is_hidden below)
    # — City Planning is not just first, it's the ONLY item they see.
    other_page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert other_page.items[0].id == WORKSPACE_ID
    assert personal.id not in {item.id for item in other_page.items}


async def test_other_users_personal_workspace_is_hidden(catalog_service, resource_repo):
    """Confirmed 2026-07-31: a personal workspace is invisible to anyone who
    can't reach it at all — the one deliberate exception to universal
    visibility. Everyone still sees their OWN personal workspace (previous
    test) and every non-personal resource stays universally visible
    regardless of access (test_catalog_no_search_returns_full_workspace_tree_
    annotated_none, unchanged)."""
    personal = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Someone Else's Sandbox", parent_id=None, owner_id="u999"
    )

    page = await catalog_service.get_catalog("u031", search=None, page=1, page_size=10)
    assert personal.id not in {item.id for item in page.items}
    assert page.total == 2  # total reflects the unfiltered universe, item is just filtered out
    assert len(page.items) == 1  # only City Planning

    # The owner still sees it.
    owner_page = await catalog_service.get_catalog("u999", search=None, page=1, page_size=10)
    assert personal.id in {item.id for item in owner_page.items}


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
