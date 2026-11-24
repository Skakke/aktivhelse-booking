"""JSON-API. Samme logikk som nettsidene, klart for en senere app eller React-klient.

Dokumentasjon genereres automatisk på /docs.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.schemas import BookingIn, BookingOut, ClassOut

router = APIRouter(prefix="/api", tags=["API"])

_STATUS = {
    services.NotFound: status.HTTP_404_NOT_FOUND,
    services.ClassFull: status.HTTP_409_CONFLICT,
    services.AlreadyBooked: status.HTTP_409_CONFLICT,
    services.ClassStarted: status.HTTP_409_CONFLICT,
    services.CancelTooLate: status.HTTP_409_CONFLICT,
}


def _out(v: services.ClassView) -> ClassOut:
    gc = v.gc
    return ClassOut(
        id=gc.id, name=gc.name, instructor=gc.instructor, department=gc.department.name, room=gc.room,
        starts_at=gc.starts_at, duration_min=gc.duration_min, capacity=gc.capacity,
        booked=v.booked, available=v.available, full=v.full,
    )


def _http(e: services.BookingError) -> HTTPException:
    return HTTPException(_STATUS.get(type(e), status.HTTP_400_BAD_REQUEST), detail=str(e))


@router.get("/classes", response_model=list[ClassOut], summary="Timeplan")
def list_classes(department_id: int | None = None, day: date | None = None,
                 db: Session = Depends(get_db)):
    return [_out(v) for v in services.list_classes(db, department_id, day)]


@router.get("/classes/{class_id}", response_model=ClassOut, summary="Én time")
def get_class(class_id: int, db: Session = Depends(get_db)):
    try:
        return _out(services.get_class(db, class_id))
    except services.BookingError as e:
        raise _http(e) from None


@router.post("/classes/{class_id}/bookings", response_model=BookingOut,
             status_code=status.HTTP_201_CREATED, summary="Meld på",
             responses={404: {"description": "Timen finnes ikke"},
                        409: {"description": "Full, allerede påmeldt eller startet"}})
def create_booking(class_id: int, data: BookingIn, db: Session = Depends(get_db)):
    try:
        return services.book(db, class_id, data)
    except services.BookingError as e:
        raise _http(e) from None


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Meld av",
               responses={404: {"description": "Finnes ikke eller feil medlemsnummer"},
                          409: {"description": "Avmeldingsfristen er passert"}})
def delete_booking(booking_id: int, member_number: str, db: Session = Depends(get_db)):
    try:
        services.cancel(db, booking_id, member_number)
    except services.BookingError as e:
        raise _http(e) from None
