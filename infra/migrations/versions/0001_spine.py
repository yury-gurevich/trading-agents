"""Create the PostgreSQL graph spine tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_spine"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create nodes and typed edges."""
    op.create_table(
        "nodes",
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column(
            "props",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "schema_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.PrimaryKeyConstraint("label", "key"),
    )
    op.create_table(
        "edges",
        sa.Column("parent_label", sa.Text(), nullable=False),
        sa.Column("parent_key", sa.Text(), nullable=False),
        sa.Column("child_label", sa.Text(), nullable=False),
        sa.Column("child_key", sa.Text(), nullable=False),
        sa.Column("edge_type", sa.Text(), nullable=False),
        sa.Column(
            "props",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_label", "parent_key"],
            ["nodes.label", "nodes.key"],
        ),
        sa.ForeignKeyConstraint(
            ["child_label", "child_key"],
            ["nodes.label", "nodes.key"],
        ),
        sa.PrimaryKeyConstraint(
            "parent_label",
            "parent_key",
            "child_label",
            "child_key",
            "edge_type",
        ),
    )
    op.create_index(
        "edges_child",
        "edges",
        ["child_label", "child_key", "edge_type"],
    )


def downgrade() -> None:
    """Drop the graph spine tables."""
    op.drop_index("edges_child", table_name="edges")
    op.drop_table("edges")
    op.drop_table("nodes")
