import pytest

from permissions_server.domain.entities import (
    Grantee,
    GranteeType,
    ResourceType,
    Role,
    is_organizational,
    is_valid_child,
    role_rank,
)


def test_workspace_allows_folder_map_and_layer_directly():
    assert is_valid_child(ResourceType.WORKSPACE, ResourceType.FOLDER) is True
    assert is_valid_child(ResourceType.WORKSPACE, ResourceType.MAP) is True
    assert is_valid_child(ResourceType.WORKSPACE, ResourceType.LAYER) is True
    assert is_valid_child(ResourceType.WORKSPACE, ResourceType.GROUP) is False


def test_folder_allows_folder_map_and_layer_directly():
    assert is_valid_child(ResourceType.FOLDER, ResourceType.FOLDER) is True
    assert is_valid_child(ResourceType.FOLDER, ResourceType.MAP) is True
    assert is_valid_child(ResourceType.FOLDER, ResourceType.LAYER) is True
    assert is_valid_child(ResourceType.FOLDER, ResourceType.GROUP) is False


def test_map_allows_group_and_layer_only():
    assert is_valid_child(ResourceType.MAP, ResourceType.GROUP) is True
    assert is_valid_child(ResourceType.MAP, ResourceType.LAYER) is True
    assert is_valid_child(ResourceType.MAP, ResourceType.FOLDER) is False


def test_group_nests_indefinitely():
    assert is_valid_child(ResourceType.GROUP, ResourceType.GROUP) is True
    assert is_valid_child(ResourceType.GROUP, ResourceType.LAYER) is True
    assert is_valid_child(ResourceType.GROUP, ResourceType.MAP) is False


def test_layer_is_always_a_leaf():
    for child_type in ResourceType:
        assert is_valid_child(ResourceType.LAYER, child_type) is False


def test_only_a_workspace_may_be_a_root():
    assert is_valid_child(None, ResourceType.WORKSPACE) is True
    assert is_valid_child(None, ResourceType.FOLDER) is False


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        (ResourceType.WORKSPACE, True),
        (ResourceType.FOLDER, True),
        (ResourceType.GROUP, True),
        (ResourceType.MAP, False),
        (ResourceType.LAYER, False),
    ],
)
def test_is_organizational(resource_type, expected):
    """Map/Layer are deliberately excluded even though Map can structurally
    hold children (Group/Layer) too — see entities.py's comment on
    _ORGANIZATIONAL_TYPES: that data isn't owned by this server."""
    assert is_organizational(resource_type) is expected


@pytest.mark.parametrize(
    "role,expected_rank",
    [
        (Role.VIEWER, 1),
        (Role.EDITOR, 2),
        (Role.MANAGER, 3),
        (Role.ADMIN, 4),
    ],
)
def test_role_rank_orders_viewer_below_admin(role, expected_rank):
    assert role_rank(role) == expected_rank


def test_grantee_user_type_requires_user_id_not_team_id():
    Grantee(GranteeType.USER, user_id="u001")  # valid, doesn't raise
    with pytest.raises(ValueError):
        Grantee(GranteeType.USER, team_id="team-1")
    with pytest.raises(ValueError):
        Grantee(GranteeType.USER)  # neither id set


def test_grantee_team_type_requires_team_id_not_user_id():
    Grantee(GranteeType.TEAM, team_id="team-1")  # valid, doesn't raise
    with pytest.raises(ValueError):
        Grantee(GranteeType.TEAM, user_id="u001")
    with pytest.raises(ValueError):
        Grantee(GranteeType.TEAM)  # neither id set


def test_grantee_rejects_both_ids_set_regardless_of_type():
    with pytest.raises(ValueError):
        Grantee(GranteeType.USER, user_id="u001", team_id="team-1")
