"""SQLAlchemy declarative base shared by every ORM model in infrastructure/db/models.py."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
