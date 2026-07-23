from permissions_server.domain.entities import ResourceType, is_valid_child


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
