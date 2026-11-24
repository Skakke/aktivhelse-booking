"""Administrasjon for ansatte: opprette, endre og slette timer, se deltakere.

Prototypen har ikke innlogging (se avgrensning i kravspesifikasjonen).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.schemas import ClassIn, norwegian_errors
from app.web import fmt_input, templates

router = APIRouter(prefix="/admin")

FIELDS = ("name", "instructor", "department_id", "starts_at", "duration_min", "capacity")


async def _form(request: Request) -> dict[str, str]:
    data = await request.form()
    return {f: str(data.get(f, "")).strip() for f in FIELDS}


def _admin_page(request: Request, db: Session, form: dict | None = None, errors: dict | None = None):
    ctx = {
        "classes": services.list_classes(db),
        "departments": services.list_departments(db),
        "form": form or {"duration_min": "60", "capacity": "20"},
        "errors": errors or {},
    }
    return templates.TemplateResponse(request, "admin.html", ctx, status_code=422 if errors else 200)


def _class_page(request: Request, db: Session, class_id: int, form=None, errors=None, msg=""):
    view = services.get_class(db, class_id)
    gc = view.gc
    if form is None:
        form = {
            "name": gc.name, "instructor": gc.instructor, "department_id": str(gc.department_id),
            "starts_at": fmt_input(gc.starts_at), "duration_min": str(gc.duration_min), "capacity": str(gc.capacity),
        }
    ctx = {"c": view, "departments": services.list_departments(db), "form": form,
           "errors": errors or {}, "msg": msg}
    return templates.TemplateResponse(request, "admin_class.html", ctx,
                                      status_code=422 if errors else 200)


@router.get("", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)):
    return _admin_page(request, db)


@router.post("/classes", response_class=HTMLResponse)
async def create_class(request: Request, db: Session = Depends(get_db)):
    form = await _form(request)
    try:
        services.create_class(db, ClassIn(**form))
    except ValidationError as e:
        return _admin_page(request, db, form, norwegian_errors(e))
    except services.BookingError as e:
        return _admin_page(request, db, form, {"skjema": str(e)})
    return RedirectResponse("/admin", status_code=303)


@router.get("/classes/{class_id}", response_class=HTMLResponse)
def class_detail(request: Request, class_id: int, msg: str = "", db: Session = Depends(get_db)):
    try:
        return _class_page(request, db, class_id, msg=msg)
    except services.NotFound:
        return RedirectResponse("/admin", status_code=303)


@router.post("/classes/{class_id}", response_class=HTMLResponse)
async def update_class(request: Request, class_id: int, db: Session = Depends(get_db)):
    form = await _form(request)
    try:
        services.update_class(db, class_id, ClassIn(**form))
    except ValidationError as e:
        return _class_page(request, db, class_id, form, norwegian_errors(e))
    except services.CapacityTooLow as e:
        return _class_page(request, db, class_id, form, {"capacity": str(e)})
    except services.NotFound:
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse(f"/admin/classes/{class_id}?msg=Endringene+er+lagret.", status_code=303)


@router.post("/classes/{class_id}/delete")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    try:
        services.delete_class(db, class_id)
    except services.NotFound:
        pass
    return RedirectResponse("/admin", status_code=303)


@router.post("/classes/{class_id}/bookings/{booking_id}/delete")
def remove_participant(class_id: int, booking_id: int, db: Session = Depends(get_db)):
    try:
        services.remove_booking(db, booking_id)
    except services.NotFound:
        pass
    return RedirectResponse(f"/admin/classes/{class_id}?msg=Deltakeren+er+fjernet.", status_code=303)
