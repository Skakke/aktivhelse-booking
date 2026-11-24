"""Konfigurasjon lest fra miljøvariabler (settes i compose.yaml)."""

import os
from zoneinfo import ZoneInfo

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://booking:booking@localhost:5432/booking"
)

# Alle tidspunkter lagres i UTC i databasen og vises i norsk tid.
TZ = ZoneInfo("Europe/Oslo")
