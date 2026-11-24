"""Sider for medlemmer: timeplan, påmelding og mine påmeldinger."""

from datetime import date, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.schemas import BookingIn, norwegian_errors
from app.web import templates

router = APIRouter()


def _parse_filters(department: str | None, day: str | None) -> tuple[int | None, date | None]:
    """Ugyldige filterverdier ignoreres i stedet for å gi feil."""
    dep = int(department) if department and department.isdigit() else None
    try:
        d = date.fromisoformat(day) if day else None
    except ValueError:
        d = None
    return dep, d


def _schedule_context(db: Session, department: str | None, day: str | None) -> dict:
    dep, d = _parse_filters(department, day)
    today = services.now().date()
    return {
        "classes": services.list_classes(db, dep, d),
        "departments": services.list_departments(db),
        "days": [today + timedelta(days=i) for i in range(7)],
        "selected_department": dep,
        "selected_day": d,
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request, department: str | None = None, day: str | None = None,
          db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "index.html", _schedule_context(db, department, day))


@router.get("/classes", response_class=HTMLResponse)
def class_list(request: Request, department: str | None = None, day: str | None = None,
               db: Session = Depends(get_db)):
    """HTMX: bare listen, brukes når filter endres eller etter en påmelding."""
    return templates.TemplateResponse(
        request, "partials/class_list.html", _schedule_context(db, department, day)
    )


@router.get("/classes/{class_id}/book", response_class=HTMLResponse)
def booking_form(request: Request, class_id: int, db: Session = Depends(get_db)):
    try:
        view = services.get_class(db, class_id)
    except services.NotFound as e:
        return templates.TemplateResponse(request, "partials/message.html", {"error": str(e)})
    return templates.TemplateResponse(
        request, "partials/booking_form.html", {"c": view, "form": {}, "errors": {}}
    )


@router.post("/classes/{class_id}/book", response_class=HTMLResponse)
def submit_booking(request: Request, class_id: int, name: str = Form(""), email: str = Form(""),
                   db: Session = Depends(get_db)):
    form = {"name": name, "email": email}
    try:
        view = services.get_class(db, class_id)
    except services.NotFound as e:
        return templates.TemplateResponse(request, "partials/message.html", {"error": str(e)})

    try:
        data = BookingIn(**form)
        booking = services.book(db, class_id, data)
    except ValidationError as e:
        ctx = {"c": view, "form": form, "errors": norwegian_errors(e)}
        return templates.TemplateResponse(request, "partials/booking_form.html", ctx)
    except services.BookingError as e:
        ctx = {"c": services.get_class(db, class_id), "form": form, "errors": {"skjema": str(e)}}
        response = templates.TemplateResponse(request, "partials/booking_form.html", ctx)
        response.headers["HX-Trigger"] = "classesChanged"
        return response

    response = templates.TemplateResponse(
        request, "partials/booking_done.html", {"c": view, "booking": booking}
    )
    # Ber timeplanen om å hente seg selv på nytt, så ledige plasser oppdateres.
    response.headers["HX-Trigger"] = "classesChanged"
    return response


@router.get("/mine", response_class=HTMLResponse)
def my_bookings(request: Request, email: str = "", msg: str = "", db: Session = Depends(get_db)):
    bookings = services.bookings_for_email(db, email) if email.strip() else []
    return templates.TemplateResponse(
        request, "my_bookings.html", {"email": email.strip(), "bookings": bookings, "msg": msg}
    )


@router.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, email: str = Form(""), db: Session = Depends(get_db)):
    try:
        services.cancel(db, booking_id, email)
        msg = "Du er meldt av timen."
    except services.BookingError as e:
        msg = str(e)
    return RedirectResponse(f"/mine?{urlencode({'email': email, 'msg': msg})}", status_code=303)
