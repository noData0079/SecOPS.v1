"""Initial DB schema for SecOps AI.

Creates the primary `issues` table used by the SecOps console.

Revision ID: 0001_initial
Revises: None
Create Date: 2025-11-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "issues",
        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
            nullable=False,
            comment="Issue id (UUID string).",
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
            comment="Short human-readable title for the issue.",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Detailed description of the issue / finding.",
        ),
        sa.Column(
            "severity",
            sa.String(length=32),
            nullable=False,
            server_default="medium",
            comment="Severity: critical, high, medium, low, info.",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="open",
            comment="Status: open, in_progress, resolved, ignored, etc.",
        ),
        sa.Column(
            "source",
            sa.String(length=64),
            nullable=True,
            comment="Source system: github, k8s, ci, scanner, manual, etc.",
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Timestamp when the issue was first detected.",
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the issue was resolved (if any).",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Arbitrary structured metadata (links, payloads, etc.).",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation time.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="Last update timestamp.",
        ),
        sa.UniqueConstraint("id", name="uq__issues__id"),
    )

    op.create_index("ix__issues__severity", "issues", ["severity"])
    op.create_index("ix__issues__status", "issues", ["status"])
    op.create_index("ix__issues__source", "issues", ["source"])
    op.create_index("ix__issues__detected_at", "issues", ["detected_at"])


def downgrade() -> None:
    op.drop_index("ix__issues__detected_at", table_name="issues")
    op.drop_index("ix__issues__source", table_name="issues")
    op.drop_index("ix__issues__status", table_name="issues")
    op.drop_index("ix__issues__severity", table_name="issues")
    op.drop_table("issues")
