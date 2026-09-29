"""Domain-level errors. api/ translates these into HTTP responses.

Every error carries a stable, language-neutral ``code`` (plus optional
``params`` for placeholders) alongside its English message, so clients can
render the error in their own UI language — the backend never localizes.
Each subclass supplies a generic default code; raise sites pass a specific
one only where the client can show a more helpful message than the generic.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain/application errors."""

    default_code = "error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        params: dict[str, str | int] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code or self.default_code
        self.params: dict[str, str | int] = params or {}


class NotFoundError(DomainError):
    default_code = "not_found"


class UnauthorizedError(DomainError):
    """Missing, malformed, or expired token — api/ maps this to 401."""

    default_code = "unauthorized"


class ForbiddenError(DomainError):
    """Authenticated, but not permitted for this action — api/ maps this to 403."""

    default_code = "forbidden"


class ConflictError(DomainError):
    default_code = "conflict"
