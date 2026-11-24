"""Første versjon: avdelinger, gruppetimer og påmeldinger

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "group_classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("instructor", sa.String(100), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_capacity_positive"),
        sa.CheckConstraint("duration_min > 0", name="ck_duration_positive"),
    )
    op.create_index("ix_group_classes_starts_at", "group_classes", ["starts_at"])
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_id", sa.Integer(),
                  sa.ForeignKey("group_classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("class_id", "email", name="uq_booking_class_email"),
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_index("ix_group_classes_starts_at", table_name="group_classes")
    op.drop_table("group_classes")
    op.drop_table("departments")
