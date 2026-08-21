"""Exercises SqlAlchemyResourceRepository against real Postgres — in
particular the raw-SQL ltree paths (path_to_root, move, descendant_ids,
delete) that infrastructure/db/types.py's Ltree type and the `ltree`
extension itself are the only things capable of running."""

from __future__ import annotations

from permissions_server.domain.entities import ResourceType


async def test_create_root_workspace_has_single_label_path(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    assert ws.parent_id is None
    path = await resource_repo.path_to_root(ws.id)
    assert [r.id for r in path] == [ws.id]


async def test_create_child_extends_parent_path(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    folder = await resource_repo.create(type=ResourceType.FOLDER, name="Docs", parent_id=ws.id)
    layer = await resource_repo.create(type=ResourceType.LAYER, name="Roads", parent_id=folder.id)

    path = await resource_repo.path_to_root(layer.id)
    # root-first, nearest-last — AccessResolver._walk_up relies on this order.
    assert [r.id for r in path] == [ws.id, folder.id, layer.id]


async def test_get_by_id_missing_returns_none(resource_repo):
    assert await resource_repo.get_by_id("does-not-exist") is None


async def test_children_of_orders_by_name(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    await resource_repo.create(type=ResourceType.FOLDER, name="Zebra", parent_id=ws.id)
    await resource_repo.create(type=ResourceType.FOLDER, name="Alpha", parent_id=ws.id)

    children = await resource_repo.children_of(ws.id)
    assert [c.name for c in children] == ["Alpha", "Zebra"]


async def test_descendant_ids_includes_self_and_every_level(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    folder = await resource_repo.create(type=ResourceType.FOLDER, name="Docs", parent_id=ws.id)
    layer = await resource_repo.create(type=ResourceType.LAYER, name="Roads", parent_id=folder.id)

    descendants = set(await resource_repo.descendant_ids(ws.id))
    assert descendants == {ws.id, folder.id, layer.id}


async def test_delete_cascades_whole_subtree(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    folder = await resource_repo.create(type=ResourceType.FOLDER, name="Docs", parent_id=ws.id)
    layer = await resource_repo.create(type=ResourceType.LAYER, name="Roads", parent_id=folder.id)

    await resource_repo.delete(folder.id)

    assert await resource_repo.get_by_id(folder.id) is None
    assert await resource_repo.get_by_id(layer.id) is None
    assert await resource_repo.get_by_id(ws.id) is not None


async def test_move_reattaches_subtree_under_new_parent(resource_repo):
    ws_a = await resource_repo.create(type=ResourceType.WORKSPACE, name="A", parent_id=None)
    ws_b = await resource_repo.create(type=ResourceType.WORKSPACE, name="B", parent_id=None)
    folder = await resource_repo.create(type=ResourceType.FOLDER, name="Docs", parent_id=ws_a.id)
    layer = await resource_repo.create(type=ResourceType.LAYER, name="Roads", parent_id=folder.id)

    await resource_repo.move(folder.id, ws_b.id)

    moved_folder = await resource_repo.get_by_id(folder.id)
    assert moved_folder.parent_id == ws_b.id

    # the layer nested under the moved folder must have followed it — its
    # ancestor chain is now rooted at ws_b, not ws_a.
    layer_path = await resource_repo.path_to_root(layer.id)
    assert [r.id for r in layer_path] == [ws_b.id, folder.id, layer.id]


async def test_list_page_filters_by_search_case_insensitively(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    await resource_repo.create(type=ResourceType.FOLDER, name="Infrastructure", parent_id=ws.id)
    await resource_repo.create(type=ResourceType.FOLDER, name="Land Use", parent_id=ws.id)

    page = await resource_repo.list_page(search="infra", page=1, page_size=10)
    assert [r.name for r in page.items] == ["Infrastructure"]
    assert page.total == 1


async def test_list_by_type_pinned_id_sorts_first(resource_repo):
    ws1 = await resource_repo.create(type=ResourceType.WORKSPACE, name="Zebra", parent_id=None)
    ws2 = await resource_repo.create(type=ResourceType.WORKSPACE, name="Alpha", parent_id=None)

    page = await resource_repo.list_by_type(
        ResourceType.WORKSPACE, page=1, page_size=10, pinned_id=ws1.id
    )
    assert [r.id for r in page.items][0] == ws1.id
    assert ws2.id in [r.id for r in page.items]


async def test_set_inherits_from_parent_persists(resource_repo):
    ws = await resource_repo.create(type=ResourceType.WORKSPACE, name="Root", parent_id=None)
    updated = await resource_repo.set_inherits_from_parent(ws.id, False)
    assert updated.inherits_from_parent is False

    reloaded = await resource_repo.get_by_id(ws.id)
    assert reloaded.inherits_from_parent is False


async def test_find_workspace_by_owner(resource_repo):
    ws = await resource_repo.create(
        type=ResourceType.WORKSPACE, name="Dana's Workspace", parent_id=None, owner_id="u001"
    )
    found = await resource_repo.find_workspace_by_owner("u001")
    assert found.id == ws.id
    assert await resource_repo.find_workspace_by_owner("no-such-user") is None
