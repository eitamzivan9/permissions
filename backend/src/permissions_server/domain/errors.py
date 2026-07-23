"""Domain-level errors. api/ translates these into HTTP responses."""


class DomainError(Exception):
    """Base class for all domain/application errors."""


class NotFoundError(DomainError):
    pass


class UnauthorizedError(DomainError):
    """Missing, malformed, or expired token — api/ maps this to 401."""

    pass


class ForbiddenError(DomainError):
    """Authenticated, but not permitted for this action — api/ maps this to 403."""

    pass


class ConflictError(DomainError):
    pass
