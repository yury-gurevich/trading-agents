"""Baseline revision — empty initial migration.

There are no domain tables yet (Sprint 02 establishes the pipeline only).
Each agent's store.py will add its own tables in subsequent migrations.

Revision ID: 0001
Revises:
Create Date: 2026-06-06 00:00:00.000000+00:00
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Apply the baseline (no-op: no tables exist yet)."""


def downgrade() -> None:
    """Revert the baseline (no-op)."""
