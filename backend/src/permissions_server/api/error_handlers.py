"""Translates domain/errors.py exceptions into HTTP responses, in one place —
individual routers just raise domain errors, never construct HTTPException
for these cases themselves."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from permissions_server.domain.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

_STATUS_BY_ERROR_TYPE: list[tuple[type[DomainError], int]] = [
    (UnauthorizedError, status.HTTP_401_UNAUTHORIZED),
    (ForbiddenError, status.HTTP_403_FORBIDDEN),
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (ConflictError, status.HTTP_409_CONFLICT),
]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code = status.HTTP_400_BAD_REQUEST
        for error_type, code in _STATUS_BY_ERROR_TYPE:
            if isinstance(exc, error_type):
                status_code = code
                break
        # `detail` stays English for API callers; `code`/`params` let a UI
        # render the error in its own language (see domain/errors.py).
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc), "code": exc.code, "params": exc.params},
        )
