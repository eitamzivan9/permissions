"""Wraps adfs-auth's testing.MockTokenAcquirer behind the TokenIssuer port."""

from __future__ import annotations

from adfs_auth.testing import MockTokenAcquirer

from permissions_server.config import get_settings
from permissions_server.domain.entities import AuthenticatedUser


class AdfsAuthMockTokenIssuer:
    """TokenIssuer backed by the adfs-auth library's MockTokenAcquirer — delegates
    mock JWT minting to the library instead of hand-rolling jwt.encode here.
    Replaced (not edited around) by a real ADFS OidcAuthorizationCodeAcquirer-backed
    flow in Phase 2, once this app itself needs to acquire tokens rather than just
    validate them it already receives."""

    def __init__(self) -> None:
        settings = get_settings()
        self._acquirer = MockTokenAcquirer(
            settings.jwt_secret,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            token_ttl_seconds=settings.jwt_expire_minutes * 60,
        )

    async def issue(self, user: AuthenticatedUser) -> str:
        # MockTokenAcquirer speaks the OIDC start/complete-login shape; `code`
        # stands in for the user id being logged in as (see adfs-auth's GUIDE.md).
        # There's no real redirect here — start_login/complete_login are called
        # back-to-back to mint a token immediately, matching this app's own
        # "pick a mock user, get a token" login flow.
        challenge = await self._acquirer.start_login()
        result = await self._acquirer.complete_login(
            code=user.id,
            state=challenge.state,
            expected_state=challenge.state,
            code_verifier=challenge.code_verifier,
        )
        return result.id_token
