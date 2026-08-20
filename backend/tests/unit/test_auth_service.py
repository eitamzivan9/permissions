import pytest

from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.errors import NotFoundError, UnauthorizedError
from permissions_server.infrastructure.auth.adfs_auth_mock_issuer import AdfsAuthMockTokenIssuer
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


async def test_validate_rejects_a_well_signed_token_for_an_unknown_subject():
    """AuthService.login() itself guards against issuing a token for an
    unknown user, but the validator must independently reject one too — a
    well-signed token whose subject isn't in the UserDirectory (e.g. minted
    directly against the issuer, bypassing AuthService) must not resolve."""
    ghost = AuthenticatedUser(id="ghost-user", name="Ghost", email="ghost@example.com")
    token = await AdfsAuthMockTokenIssuer().issue(ghost)
    with pytest.raises(UnauthorizedError):
        await AdfsAuthMockTokenValidator(MockUserDirectory()).validate(token)


async def test_search_users_matches_by_name_or_email_substring():
    directory = MockUserDirectory()
    by_name = await directory.search_users("beltran")
    assert any(u.id == "u016" for u in by_name)

    by_email = await directory.search_users("ana.beltran@geoteam.example")
    assert any(u.id == "u016" for u in by_email)

    assert await directory.search_users("zzz-nobody-matches-this") == []
