"""Tester for kravene i kravspesifikasjonen (FK = funksjonelt krav, IFK = ikke-funksjonelt)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app import services
from app.schemas import BookingIn

from .conftest import TestSession


def booking(name="Anne Johansen", email="anne@example.no"):
    return BookingIn(name=name, email=email)


# FK1: timeoversikt
def test_list_shows_available_spots(db, make_class):
    gc = make_class(capacity=5)
    services.book(db, gc.id, booking())
    [view] = services.list_classes(db)
    assert view.booked == 1
    assert view.available == 4


# FK2: påmelding
def test_book_valid_participant(db, make_class):
    gc = make_class()
    b = services.book(db, gc.id, booking(email="Anne@Example.no"))
    assert b.id is not None
    assert b.email == "anne@example.no"  # lagres med små bokstaver


# FK3: kapasitet
def test_cannot_book_full_class(db, make_class):
    gc = make_class(capacity=1)
    services.book(db, gc.id, booking())
    with pytest.raises(services.ClassFull):
        services.book(db, gc.id, booking(email="per@example.no"))


# IFK1: samtidige påmeldinger på siste plass gir aldri overbooking
def test_concurrent_bookings_never_overbook(make_class):
    gc = make_class(capacity=3)

    def attempt(i: int) -> bool:
        with TestSession() as session:
            try:
                services.book(session, gc.id, booking(email=f"medlem{i}@example.no"))
                return True
            except services.ClassFull:
                return False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(20)))

    assert sum(results) == 3
    with TestSession() as session:
        assert services.get_class(session, gc.id).booked == 3


# FK4: ingen dobbeltbooking
def test_same_email_twice_is_rejected(db, make_class):
    gc = make_class()
    services.book(db, gc.id, booking())
    with pytest.raises(services.AlreadyBooked):
        services.book(db, gc.id, booking(name="Anne J.", email="ANNE@example.no"))


# FK5: avmelding
def test_cancel_frees_the_spot(db, make_class):
    gc = make_class(capacity=1)
    b = services.book(db, gc.id, booking())
    services.cancel(db, b.id, "anne@example.no")
    assert services.get_class(db, gc.id).available == 1


def test_cannot_cancel_someone_elses_booking(db, make_class):
    gc = make_class()
    b = services.book(db, gc.id, booking())
    with pytest.raises(services.NotFound):
        services.cancel(db, b.id, "per@example.no")


# FK6: validering
@pytest.mark.parametrize("name,email", [
    ("", "anne@example.no"),
    ("   ", "anne@example.no"),
    ("Anne", "ikke-en-epost"),
    ("Anne", ""),
])
def test_invalid_input_is_rejected(name, email):
    with pytest.raises(ValidationError):
        BookingIn(name=name, email=email)


def test_cannot_book_started_class(db, make_class):
    gc = make_class(starts_in=timedelta(minutes=-5))
    with pytest.raises(services.ClassStarted):
        services.book(db, gc.id, booking())


def test_cannot_book_missing_class(db):
    with pytest.raises(services.NotFound):
        services.book(db, 9999, booking())


# FK7: admin kan ikke sette kapasitet under antall påmeldte
def test_capacity_cannot_go_below_booked(db, make_class):
    from app.schemas import ClassIn

    gc = make_class(capacity=5)
    services.book(db, gc.id, booking())
    services.book(db, gc.id, booking(email="per@example.no"))
    data = ClassIn(name=gc.name, instructor=gc.instructor, department_id=gc.department_id,
                   starts_at=gc.starts_at, duration_min=45, capacity=1)
    with pytest.raises(services.CapacityTooLow):
        services.update_class(db, gc.id, data)
