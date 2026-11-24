"""Jinja2-oppsett med filtre for norsk visning av datoer."""

from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import TZ

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

DAYS = ["man", "tir", "ons", "tor", "fre", "lør", "søn"]


def local(dt: datetime) -> datetime:
    return dt.astimezone(TZ)


def fmt_day(dt) -> str:
    """'ons 25.11'"""
    return f"{DAYS[dt.weekday()]} {dt:%d.%m}"


def fmt_time(dt: datetime) -> str:
    return f"{local(dt):%H:%M}"


def fmt_input(dt: datetime) -> str:
    """Verdi til <input type=datetime-local>."""
    return f"{local(dt):%Y-%m-%dT%H:%M}"


templates.env.filters.update(
    local=local, day=lambda dt: fmt_day(local(dt)), clock=fmt_time, input_dt=fmt_input
)
templates.env.globals["fmt_day"] = fmt_day
