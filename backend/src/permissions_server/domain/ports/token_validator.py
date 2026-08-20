"""Validates bearer tokens — mocked now, real ADFS OIDC validation later."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import AuthenticatedUser


class TokenValidator(Protocol):
    """Validates a bearer token and returns who it belongs to.

    Phase 2 swap point: the mock validator (backed by the adfs-auth library's
    testing.MockTokenValidator) is replaced here by a real ADFS (JWKS/RS256)
    validator via adfs-auth's oidc.OidcJwtValidator, behind this same
    interface — see CLAUDE.md.
    """

    async def validate(self, token: str) -> AuthenticatedUser: ...
