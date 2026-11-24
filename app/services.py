"""Forretningslogikk for booking.

All logikk som har med kapasitet og påmelding å gjøre ligger her, slik at
den samme koden brukes av nettsidene, API-et og testene.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.config import CANCEL_DEADLINE_HOURS, TZ
from app.models import Booking, Department, GroupClass
from app.schemas import BookingIn, ClassIn


class BookingError(Exception):
    """Basisklasse for feil som skal vises til brukeren."""

    message = "Noe gikk galt."

    def __str__(self) -> str:
        return self.message


class NotFound(BookingError):
    message = "Fant ikke timen eller påmeldingen."


class ClassFull(BookingError):
    message = "Timen er dessverre full."


class AlreadyBooked(BookingError):
    message = "Dette medlemsnummeret er allerede påmeldt timen."


class ClassStarted(BookingError):
    message = "Timen har allerede startet."


class CancelTooLate(BookingError):
    message = (
        f"Avmeldingsfristen er {CANCEL_DEADLINE_HOURS} timer før timen starter. "
        "Kontakt resepsjonen."
    )


class CapacityTooLow(BookingError):
    message = "Kapasiteten kan ikke settes lavere enn antall påmeldte."


@dataclass
class ClassView:
    """En gruppetime med beregnet belegg, klar for visning."""

    gc: GroupClass
    booked: int

    @property
    def available(self) -> int:
        return max(self.gc.capacity - self.booked, 0)

    @property
    def full(self) -> bool:
        return self.booked >= self.gc.capacity

    @property
    def started(self) -> bool:
        return self.gc.starts_at <= now()

    @property
    def bookable(self) -> bool:
        return not self.full and not self.started


def cancel_deadline(gc: GroupClass) -> datetime:
    return gc.starts_at - timedelta(hours=CANCEL_DEADLINE_HOURS)


def can_cancel(gc: GroupClass) -> bool:
    return now() < cancel_deadline(gc)


def now() -> datetime:
    return datetime.now(TZ)


def to_local(dt: datetime) -> datetime:
    """Tolker et tidspunkt uten tidssone som norsk tid."""
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt


def list_departments(db: Session) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)))


def list_classes(
    db: Session, department_id: int | None = None, day: date | None = None
) -> list[ClassView]:
    """Timeplan fra i dag og fremover, eventuelt filtrert på avdeling og dag."""
    booked = (
        select(Booking.class_id, func.count(Booking.id).label("n"))
        .group_by(Booking.class_id)
        .subquery()
    )
    stmt = (
        select(GroupClass, func.coalesce(booked.c.n, 0))
        .outerjoin(booked, booked.c.class_id == GroupClass.id)
        .options(joinedload(GroupClass.department))
        .order_by(GroupClass.starts_at)
    )
    if day:
        start = datetime.combine(day, time.min, TZ)
        stmt = stmt.where(GroupClass.starts_at >= start, GroupClass.starts_at < start + timedelta(days=1))
    else:
        stmt = stmt.where(GroupClass.starts_at >= datetime.combine(now().date(), time.min, TZ))
    if department_id:
        stmt = stmt.where(GroupClass.department_id == department_id)
    return [ClassView(gc, n) for gc, n in db.execute(stmt).all()]


def get_class(db: Session, class_id: int) -> ClassView:
    gc = db.get(GroupClass, class_id, options=[joinedload(GroupClass.department)])
    if gc is None:
        raise NotFound()
    return ClassView(gc, _count(db, class_id))


def _count(db: Session, class_id: int) -> int:
    return db.scalar(select(func.count(Booking.id)).where(Booking.class_id == class_id)) or 0


def book(db: Session, class_id: int, data: BookingIn) -> Booking:
    """Melder en deltaker på en time.

    Raden for timen låses med SELECT ... FOR UPDATE før plassene telles. Kommer
    to påmeldinger på siste plass samtidig, må den andre vente til den første
    er ferdig, og ser da at timen er full. Dermed kan timen aldri overbookes.
    """
    gc = db.scalar(select(GroupClass).where(GroupClass.id == class_id).with_for_update())
    try:
        if gc is None:
            raise NotFound()
        if gc.starts_at <= now():
            raise ClassStarted()
        exists = db.scalar(
            select(Booking.id).where(
                Booking.class_id == class_id, Booking.member_number == data.member_number
            )
        )
        if exists:
            raise AlreadyBooked()
        if _count(db, class_id) >= gc.capacity:
            raise ClassFull()
        booking = Booking(class_id=class_id, name=data.name, member_number=data.member_number)
        db.add(booking)
        db.commit()
    except IntegrityError:
        # Sikkerhetsnett: unik-nøkkelen i databasen slo til.
        db.rollback()
        raise AlreadyBooked() from None
    except BookingError:
        db.rollback()
        raise
    return booking


def cancel(db: Session, booking_id: int, member_number: str) -> None:
    """Medlemmet melder seg av. Medlemsnummeret må stemme, og fristen må ikke være passert."""
    booking = db.get(Booking, booking_id)
    if booking is None or booking.member_number != member_number.strip():
        raise NotFound()
    if not can_cancel(booking.group_class):
        raise CancelTooLate()
    db.delete(booking)
    db.commit()


def remove_booking(db: Session, booking_id: int) -> None:
    """Ansatte kan fjerne en deltaker når som helst, uten medlemsnummer og frist."""
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise NotFound()
    db.delete(booking)
    db.commit()


def bookings_for_member(db: Session, member_number: str) -> list[Booking]:
    stmt = (
        select(Booking)
        .join(Booking.group_class)
        .where(Booking.member_number == member_number.strip(), GroupClass.starts_at >= now())
        .options(joinedload(Booking.group_class).joinedload(GroupClass.department))
        .order_by(GroupClass.starts_at)
    )
    return list(db.scalars(stmt))


def create_class(db: Session, data: ClassIn) -> GroupClass:
    if db.get(Department, data.department_id) is None:
        raise NotFound()
    gc = GroupClass(**data.model_dump(exclude={"starts_at"}), starts_at=to_local(data.starts_at))
    db.add(gc)
    db.commit()
    return gc


def update_class(db: Session, class_id: int, data: ClassIn) -> GroupClass:
    gc = db.scalar(select(GroupClass).where(GroupClass.id == class_id).with_for_update())
    if gc is None or db.get(Department, data.department_id) is None:
        db.rollback()
        raise NotFound()
    if data.capacity < _count(db, class_id):
        db.rollback()
        raise CapacityTooLow()
    for field, value in data.model_dump(exclude={"starts_at"}).items():
        setattr(gc, field, value)
    gc.starts_at = to_local(data.starts_at)
    db.commit()
    return gc


def delete_class(db: Session, class_id: int) -> None:
    gc = db.get(GroupClass, class_id)
    if gc is None:
        raise NotFound()
    db.delete(gc)
    db.commit()
