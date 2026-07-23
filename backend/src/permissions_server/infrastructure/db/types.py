"""Custom SQLAlchemy type for PostgreSQL's ltree, used only by ResourceModel.path
(see infrastructure/db/models.py). No sqlalchemy-utils dependency for one type."""

from __future__ import annotations

import re

from sqlalchemy import cast
from sqlalchemy.sql.type_api import UserDefinedType

_INVALID_LABEL_CHARS = re.compile(r"[^A-Za-z0-9_]")


def sanitize_label(entity_id: str) -> str:
    """ltree labels allow only letters, digits, and underscores — resource ids
    (uuid4 hex or seed-data slugs) may contain hyphens, so those become
    underscores. Sanitization only touches fixed hyphen positions, so
    uniqueness among already-unique ids is preserved."""
    return _INVALID_LABEL_CHARS.sub("_", entity_id)


class Ltree(UserDefinedType):
    """Maps a Python str (dot-separated labels, e.g. 'ws_city.f_infra') to
    PostgreSQL's ltree column type. asyncpg has no built-in codec for ltree,
    so bind_expression wraps every bound parameter in an explicit
    CAST(... AS LTREE) — Postgres does the coercion, asyncpg just sees a
    plain text parameter."""

    cache_ok = True

    def get_col_spec(self, **kwargs: object) -> str:
        return "LTREE"

    def bind_processor(self, dialect: object) -> object:
        def process(value: str | None) -> str | None:
            return value

        return process

    def result_processor(self, dialect: object, coltype: object) -> object:
        def process(value: str | None) -> str | None:
            return value

        return process

    def bind_expression(self, bindvalue: object) -> object:
        return cast(bindvalue, self)
