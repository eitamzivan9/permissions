import pytest

from permissions_server.domain.errors import NotFoundError
from permissions_server.infrastructure.auth.adfs_auth_mock_validator import (
    AdfsAuthMockTokenValidator,
)
from permissions_server.infrastructure.auth.mock_user_directory import MockUserDirectory


async def test_login_issues_a_token_that_resolves_to_the_right_user(auth_service):
    token = await auth_service.login("u001")
    resolved = await AdfsAuthMockTokenValidator(MockUserDirectory()).validate(token)
    assert resolved.id == "u001"
    assert resolved.name == "Dana Whitfield"


async def test_login_unknown_user_raises_not_found(auth_service):
    with pytest.raises(NotFoundError):
        await auth_service.login("does-not-exist")
