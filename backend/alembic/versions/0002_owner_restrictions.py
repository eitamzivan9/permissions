"""Add resources.owner_id (personal workspaces) and the restrictions table
(whitelist gate, sibling to permission_grants).

Revision ID: 0002_owner_restrictions
Revises: 0001_initial_schema
Create Date: 2026-07-27

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
# Kept short deliberately: alembic_version.version_num defaults to VARCHAR(32)
# and 0001_initial_schema's revision id already showed that limit is real.
revision = "0002_owner_restrictions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("owner_id", sa.String(), nullable=True))
    op.create_index("ix_resources_owner_id", "resources", ["owner_id"])

    op.create_table(
        "restrictions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("grantee_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("team_id", sa.String(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("resource_id", sa.String(), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("granted_by", sa.String(), nullable=False),
        sa.Column("grantee_key", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "grantee_key", "resource_id", name="uq_restriction_grantee_resource"
        ),
    )
    op.create_index("ix_restrictions_resource_id", "restrictions", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_restrictions_resource_id", table_name="restrictions")
    op.drop_table("restrictions")
    op.drop_index("ix_resources_owner_id", table_name="resources")
    op.drop_column("resources", "owner_id")
