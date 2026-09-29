import pytest

from permissions_server.domain.entities import (
    AuthenticatedUser,
    Grantee,
    GranteeType,
    ResourceType,
    Role,
)
from permissions_server.domain.errors import ConflictError

ACTOR = AuthenticatedUser(id="u-actor", name="Actor", email="actor@geoteam.example")


async def _admin_of(grant_repo, resource_id):
    await grant_repo.upsert_grant(
        Grantee(GranteeType.USER, user_id=ACTOR.id), resource_id, Role.ADMIN, granted_by="seed"
    )


@pytest.mark.parametrize(
    "resource_type", [ResourceType.WORKSPACE, ResourceType.FOLDER, ResourceType.GROUP]
)
async def test_delete_organizational_resource_with_children_is_conflict(
    resource_service, resource_repo, grant_repo, resource_type
):
    parent_id = None if resource_type is ResourceType.WORKSPACE else "map-parent"
    if parent_id is not None:
        # Folder/Group need a valid parent to exist under; give each a
        # structurally-legal container.
        container_type = (
            ResourceType.WORKSPACE if resource_type is ResourceType.FOLDER else ResourceType.MAP
        )
        container = await resource_repo.create(type=container_type, name="container", parent_id=None)
        parent_id = container.id

    parent = await resource_repo.create(type=resource_type, name="parent", parent_id=parent_id)
    child_type = ResourceType.LAYER
    await resource_repo.create(type=child_type, name="child", parent_id=parent.id)
    await _admin_of(grant_repo, parent.id)

    with pytest.raises(ConflictError) as exc_info:
        await resource_service.delete(ACTOR, parent.id)
    assert exc_info.value.code == "delete_not_empty"
    assert exc_info.value.params == {"count": 1}

    assert await resource_repo.get_by_id(parent.id) is not None


@pytest.mark.parametrize(
    "resource_type", [ResourceType.WORKSPACE, ResourceType.FOLDER, ResourceType.GROUP]
)
async def test_delete_empty_organizational_resource_succeeds(
    resource_service, resource_repo, grant_repo, resource_type
):
    parent_id = None if resource_type is ResourceType.WORKSPACE else "map-parent"
    if parent_id is not None:
        container_type = (
            ResourceType.WORKSPACE if resource_type is ResourceType.FOLDER else ResourceType.MAP
        )
        container = await resource_repo.create(type=container_type, name="container", parent_id=None)
        parent_id = container.id

    resource = await resource_repo.create(type=resource_type, name="empty", parent_id=parent_id)
    await _admin_of(grant_repo, resource.id)

    await resource_service.delete(ACTOR, resource.id)

    assert await resource_repo.get_by_id(resource.id) is None


async def test_delete_map_with_children_still_cascades(resource_service, resource_repo, grant_repo):
    """Regression guard: Map is structurally capable of having children
    (Group/Layer) but deliberately keeps the old unconditional-cascade
    delete behavior — it must NOT be subject to the empty-check."""
    workspace = await resource_repo.create(type=ResourceType.WORKSPACE, name="ws", parent_id=None)
    map_resource = await resource_repo.create(
        type=ResourceType.MAP, name="map", parent_id=workspace.id
    )
    layer = await resource_repo.create(
        type=ResourceType.LAYER, name="layer", parent_id=map_resource.id
    )
    await _admin_of(grant_repo, map_resource.id)

    await resource_service.delete(ACTOR, map_resource.id)

    assert await resource_repo.get_by_id(map_resource.id) is None
    assert await resource_repo.get_by_id(layer.id) is None


async def test_delete_layer_with_no_children_succeeds(resource_service, resource_repo, grant_repo):
    workspace = await resource_repo.create(type=ResourceType.WORKSPACE, name="ws", parent_id=None)
    layer = await resource_repo.create(type=ResourceType.LAYER, name="layer", parent_id=workspace.id)
    await _admin_of(grant_repo, layer.id)

    await resource_service.delete(ACTOR, layer.id)

    assert await resource_repo.get_by_id(layer.id) is None
