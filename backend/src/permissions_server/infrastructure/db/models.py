"""SQLAlchemy ORM models — the Postgres-facing mirror of domain/entities.py.
Column shapes match the dataclasses exactly; nothing here is imported by
domain/ or application/ (DIP: only infrastructure/repositories/ depends on
this module)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from permissions_server.domain.entities import (
    AuditAction,
    GranteeType,
    Role,
    ResourceType,
    SystemRole,
)
from permissions_server.infrastructure.db.base import Base
from permissions_server.infrastructure.db.types import Ltree


def _enum(python_enum: type) -> SqlEnum:
    # native_enum=False -> VARCHAR + Python-side validation, not a Postgres
    # native enum type. Adding a resource/role/etc. value later is then a
    # one-line change to the Python enum, not an ALTER TYPE migration.
    return SqlEnum(python_enum, native_enum=False, values_callable=lambda e: [m.value for m in e])


class ResourceModel(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[ResourceType] = mapped_column(_enum(ResourceType), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("resources.id"), nullable=True
    )
    inherits_from_parent: Mapped[bool] = mapped_column(nullable=False, default=True)
    path: Mapped[str] = mapped_column(Ltree, nullable=False)

    __table_args__ = (
        Index("ix_resources_parent_id", "parent_id"),
        Index("ix_resources_path", "path", postgresql_using="gist"),
    )


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)


class TeamMembershipModel(Base):
    __tablename__ = "team_memberships"

    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, primary_key=True)


class PermissionGrantModel(Base):
    __tablename__ = "permission_grants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    grantee_type: Mapped[GranteeType] = mapped_column(_enum(GranteeType), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id"), nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role), nullable=False)
    granted_by: Mapped[str] = mapped_column(String, nullable=False)

    # A plain composite UNIQUE(grantee_type, user_id, team_id, resource_id)
    # would NOT reliably prevent duplicates: standard SQL unique constraints
    # don't treat two NULLs as equal, so two rows sharing the same non-null
    # user_id but both having team_id=NULL aren't caught. grantee_key encodes
    # the exact (grantee, resource_id) dict key the in-memory repo uses, as
    # one always-non-null string, so the unique index actually enforces it.
    grantee_key: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("grantee_key", "resource_id", name="uq_grant_grantee_resource"),
        Index("ix_permission_grants_resource_id", "resource_id"),
    )


class SystemRoleModel(Base):
    __tablename__ = "system_roles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[SystemRole] = mapped_column(_enum(SystemRole), primary_key=True)


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    grantee_type: Mapped[GranteeType] = mapped_column(_enum(GranteeType), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    team_id: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role), nullable=False)
    action: Mapped[AuditAction] = mapped_column(_enum(AuditAction), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_log_resource_id", "resource_id"),
        Index("ix_audit_log_actor_id", "actor_id"),
    )
