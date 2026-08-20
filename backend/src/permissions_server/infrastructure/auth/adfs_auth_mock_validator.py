"""Wraps adfs-auth's testing.MockTokenValidator behind the TokenValidator port, resolving name/email via UserDirectory."""

from __future__ import annotations

from adfs_auth import InvalidTokenError as AdfsInvalidTokenError
from adfs_auth.testing import MockTokenValidator

from permissions_server.config import get_settings
from permissions_server.domain.entities import AuthenticatedUser
from permissions_server.domain.errors import UnauthorizedError
from permissions_server.domain.ports.user_directory import UserDirectory


class AdfsAuthMockTokenValidator:
    """TokenValidator backed by the adfs-auth library's MockTokenValidator.

    The library only ever proves the token's `sub` claim (plus iss/aud/exp) — its
    mock flow doesn't mint name/email claims, and per adfs-auth's own rule, mapping
    its generic AuthenticatedIdentity into THIS app's AuthenticatedUser is this app's
    job, not the library's. So this adapter resolves the full user via
    UserDirectory, the same directory AuthService already uses — not an extra
    dependency, just a lookup this class also needs.
    """

    def __init__(self, user_directory: UserDirectory) -> None:
        settings = get_settings()
        self._validator = MockTokenValidator(
            settings.jwt_secret, issuer=settings.jwt_issuer, audience=settings.jwt_audience
        )
        self._user_directory = user_directory

    async def validate(self, token: str) -> AuthenticatedUser:
        try:
            identity = await self._validator.validate(token)
        except AdfsInvalidTokenError as exc:
            raise UnauthorizedError(str(exc)) from exc

        user = await self._user_directory.get_user(identity.subject)
        if user is None:
            raise UnauthorizedError(f"token subject {identity.subject!r} is not a known user")
        return user
