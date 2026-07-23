"""Shared offset/limit + count logic for every SQLAlchemy repo that pages a
`select()` — avoids re-deriving the same count-then-slice query per entity."""

from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

M = TypeVar("M")


async def paginate(
    session: AsyncSession, stmt: Select[tuple[M]], *, page: int, page_size: int
) -> tuple[list[M], int]:
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size)))
        .scalars()
        .all()
    )
    return list(rows), total
