"""Oppstartspunkt for applikasjonen."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.db import engine
from app.routers import admin, api, public

app = FastAPI(
    title="AktivHelse gruppetimebooking",
    description="Prototype av bookingsystem for gruppetimer.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/health", tags=["Drift"], summary="Helsesjekk")
def health() -> dict[str, str]:
    """Sjekker at appen kjører og når databasen."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
