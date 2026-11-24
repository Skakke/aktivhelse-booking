"""Konfigurasjon lest fra miljøvariabler (settes i compose.yaml)."""

import os
from zoneinfo import ZoneInfo

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://booking:booking@localhost:5432/booking"
)

# Alle tidspunkter lagres i UTC i databasen og vises i norsk tid.
TZ = ZoneInfo("Europe/Oslo")

# Medlemmer kan melde seg av fram til så mange timer før timen starter.
# Ansatte kan alltid fjerne deltakere.
CANCEL_DEADLINE_HOURS = int(os.getenv("CANCEL_DEADLINE_HOURS", "2"))
