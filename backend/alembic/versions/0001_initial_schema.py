"""Initial schema: resources (ltree), teams, team_memberships,
permission_grants, system_roles, audit_log.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-23

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from permissions_server.infrastructure.db.types import Ltree

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")

    op.create_table(
        "resources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), sa.ForeignKey("resources.id"), nullable=True),
        sa.Column("inherits_from_parent", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("path", Ltree(), nullable=False),
    )
    op.create_index("ix_resources_parent_id", "resources", ["parent_id"])
    op.create_index(
        "ix_resources_path", "resources", ["path"], postgresql_using="gist"
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "team_memberships",
        sa.Column("team_id", sa.String(), sa.ForeignKey("teams.id"), primary_key=True),
        sa.Column("user_id", sa.String(), primary_key=True),
    )

    op.create_table(
        "permission_grants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("grantee_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("team_id", sa.String(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("resource_id", sa.String(), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("granted_by", sa.String(), nullable=False),
        sa.Column("grantee_key", sa.String(), nullable=False),
        sa.UniqueConstraint("grantee_key", "resource_id", name="uq_grant_grantee_resource"),
    )
    op.create_index(
        "ix_permission_grants_resource_id", "permission_grants", ["resource_id"]
    )

    op.create_table(
        "system_roles",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("role", sa.String(), primary_key=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("grantee_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("team_id", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_resource_id", "audit_log", ["resource_id"])
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("system_roles")
    op.drop_index("ix_permission_grants_resource_id", table_name="permission_grants")
    op.drop_table("permission_grants")
    op.drop_table("team_memberships")
    op.drop_table("teams")
    op.drop_index("ix_resources_path", table_name="resources")
    op.drop_index("ix_resources_parent_id", table_name="resources")
    op.drop_table("resources")
