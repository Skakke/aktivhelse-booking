"""Medlemsnummer i stedet for e-post, og sal på hver time

Endret etter kundens avklaringer 24.11: medlemmer identifiseres med navn og
medlemsnummer, og kapasiteten varierer mellom saler.

Eksisterende påmeldinger slettes, fordi de mangler medlemsnummer. Prototypen
har bare testdata, som legges inn på nytt ved oppstart.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "group_classes",
        sa.Column("room", sa.String(50), nullable=False, server_default="Sal 1"),
    )
    op.alter_column("group_classes", "room", server_default=None)

    op.execute("DELETE FROM bookings")
    op.drop_constraint("uq_booking_class_email", "bookings", type_="unique")
    op.drop_column("bookings", "email")
    op.add_column("bookings", sa.Column("member_number", sa.String(10), nullable=False))
    op.create_index("ix_bookings_member_number", "bookings", ["member_number"])
    op.create_unique_constraint(
        "uq_booking_class_member", "bookings", ["class_id", "member_number"]
    )


def downgrade() -> None:
    op.execute("DELETE FROM bookings")
    op.drop_constraint("uq_booking_class_member", "bookings", type_="unique")
    op.drop_index("ix_bookings_member_number", table_name="bookings")
    op.drop_column("bookings", "member_number")
    op.add_column("bookings", sa.Column("email", sa.String(254), nullable=False))
    op.create_unique_constraint("uq_booking_class_email", "bookings", ["class_id", "email"])
    op.drop_column("group_classes", "room")
