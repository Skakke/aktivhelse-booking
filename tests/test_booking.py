"""Tester for kravene i kravspesifikasjonen (FK = funksjonelt krav, IFK = ikke-funksjonelt)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app import services
from app.config import CANCEL_DEADLINE_HOURS
from app.schemas import BookingIn, ClassIn

from .conftest import TestSession


def booking(name="Anne Johansen", member_number="100001"):
    return BookingIn(name=name, member_number=member_number)


# FK2: timeoversikt med ledige plasser
def test_list_shows_available_spots(db, make_class):
    gc = make_class(capacity=5)
    services.book(db, gc.id, booking())
    [view] = services.list_classes(db)
    assert view.booked == 1
    assert view.available == 4


# FK1: avdelingsvalg
def test_filter_by_department(db, make_class, department):
    from app.models import Department

    other = Department(name="Nord")
    db.add(other)
    db.commit()
    make_class(name="Spinning")
    gc = make_class(name="Yoga")
    gc.department_id = other.id
    db.commit()
    assert [v.gc.name for v in services.list_classes(db, department_id=other.id)] == ["Yoga"]


# FK3: påmelding
def test_book_valid_participant(db, make_class):
    gc = make_class()
    b = services.book(db, gc.id, booking(member_number=" 100001 "))
    assert b.id is not None
    assert b.member_number == "100001"


# FK4: kapasitet
def test_cannot_book_full_class(db, make_class):
    gc = make_class(capacity=1)
    services.book(db, gc.id, booking())
    with pytest.raises(services.ClassFull):
        services.book(db, gc.id, booking(member_number="100002"))


# IFK1: samtidige påmeldinger på siste plass gir aldri overbooking
def test_concurrent_bookings_never_overbook(make_class):
    gc = make_class(capacity=3)

    def attempt(i: int) -> bool:
        with TestSession() as session:
            try:
                services.book(session, gc.id, booking(member_number=f"2000{i:02d}"))
                return True
            except services.ClassFull:
                return False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(20)))

    assert sum(results) == 3
    with TestSession() as session:
        assert services.get_class(session, gc.id).booked == 3


# FK5: ingen dobbeltpåmelding
def test_same_member_twice_is_rejected(db, make_class):
    gc = make_class()
    services.book(db, gc.id, booking())
    with pytest.raises(services.AlreadyBooked):
        services.book(db, gc.id, booking(name="Anne J."))


# FK6: avmelding gjør plassen ledig
def test_cancel_frees_the_spot(db, make_class):
    gc = make_class(capacity=1)
    b = services.book(db, gc.id, booking())
    services.cancel(db, b.id, "100001")
    assert services.get_class(db, gc.id).available == 1


def test_cannot_cancel_someone_elses_booking(db, make_class):
    gc = make_class()
    b = services.book(db, gc.id, booking())
    with pytest.raises(services.NotFound):
        services.cancel(db, b.id, "100002")


# FK7: avmeldingsfrist
def test_cannot_cancel_after_deadline(db, make_class):
    gc = make_class(starts_in=timedelta(hours=CANCEL_DEADLINE_HOURS) - timedelta(minutes=10))
    b = services.book(db, gc.id, booking())
    with pytest.raises(services.CancelTooLate):
        services.cancel(db, b.id, "100001")


def test_staff_can_remove_after_deadline(db, make_class):
    gc = make_class(starts_in=timedelta(minutes=30))
    b = services.book(db, gc.id, booking())
    services.remove_booking(db, b.id)
    assert services.get_class(db, gc.id).booked == 0


# FK9: validering
@pytest.mark.parametrize("name,member_number", [
    ("", "100001"),
    ("   ", "100001"),
    ("Anne", ""),
    ("Anne", "12"),
    ("Anne", "abc123"),
    ("Anne", "12345678901"),
])
def test_invalid_input_is_rejected(name, member_number):
    with pytest.raises(ValidationError):
        BookingIn(name=name, member_number=member_number)


def test_cannot_book_started_class(db, make_class):
    gc = make_class(starts_in=timedelta(minutes=-5))
    with pytest.raises(services.ClassStarted):
        services.book(db, gc.id, booking())


def test_cannot_book_missing_class(db):
    with pytest.raises(services.NotFound):
        services.book(db, 9999, booking())


# FK8: administrasjon – kapasitet kan ikke settes under antall påmeldte
def test_capacity_cannot_go_below_booked(db, make_class):
    gc = make_class(capacity=5)
    services.book(db, gc.id, booking())
    services.book(db, gc.id, booking(member_number="100002"))
    data = ClassIn(name=gc.name, instructor=gc.instructor, department_id=gc.department_id,
                   room=gc.room, starts_at=gc.starts_at, duration_min=45, capacity=1)
    with pytest.raises(services.CapacityTooLow):
        services.update_class(db, gc.id, data)
