"""ORM-modeller: avdelinger, gruppetimer og påmeldinger."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    classes: Mapped[list["GroupClass"]] = relationship(back_populates="department")


class GroupClass(Base):
    __tablename__ = "group_classes"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_capacity_positive"),
        CheckConstraint("duration_min > 0", name="ck_duration_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    instructor: Mapped[str] = mapped_column(String(100))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    room: Mapped[str] = mapped_column(String(50))
    duration_min: Mapped[int]
    capacity: Mapped[int]

    department: Mapped[Department] = relationship(back_populates="classes")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="group_class", cascade="all, delete-orphan", order_by="Booking.created_at"
    )


class Booking(Base):
    __tablename__ = "bookings"
    # Databasen selv hindrer at samme medlem meldes på samme time to ganger.
    __table_args__ = (
        UniqueConstraint("class_id", "member_number", name="uq_booking_class_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("group_classes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    member_number: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group_class: Mapped[GroupClass] = relationship(back_populates="bookings")
