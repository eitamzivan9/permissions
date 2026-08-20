"""Issues bearer tokens — mocked now, real ADFS OIDC acquisition later."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import AuthenticatedUser


class TokenIssuer(Protocol):
    """Issues a bearer token for a user. Only the mock auth flow implements this —
    real ADFS never issues tokens for us, it only validates ones it issued itself.

    Takes the full user (not just an id) so name/email can be embedded as token
    claims, letting TokenValidator.validate() return a full AuthenticatedUser from
    the token alone, with no extra directory lookup on every request."""

    async def issue(self, user: AuthenticatedUser) -> str: ...
