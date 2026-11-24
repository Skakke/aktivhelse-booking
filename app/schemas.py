"""Pydantic-skjemaer for validering av inndata og JSON-svar fra API-et."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

# Antatt format: 4–10 siffer. Justeres når kundens medlemsregister er kjent.
MEMBER_NUMBER_PATTERN = r"^\d{4,10}$"


class BookingIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    member_number: str = Field(pattern=MEMBER_NUMBER_PATTERN)

    @field_validator("name", "member_number", mode="before")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class ClassIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    instructor: str = Field(min_length=2, max_length=100)
    department_id: int
    room: str = Field(min_length=1, max_length=50)
    starts_at: datetime
    duration_min: int = Field(ge=15, le=240)
    capacity: int = Field(ge=1, le=200)

    @field_validator("name", "instructor", "room", mode="before")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    instructor: str
    department: str
    room: str
    starts_at: datetime
    duration_min: int
    capacity: int
    booked: int
    available: int
    full: bool


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    name: str
    member_number: str


# Norske feilmeldinger for feltene brukerne fyller ut.
_FIELD_NAMES = {
    "name": "Navn",
    "member_number": "Medlemsnummer",
    "room": "Sal",
    "instructor": "Instruktør",
    "department_id": "Avdeling",
    "starts_at": "Starttidspunkt",
    "duration_min": "Varighet",
    "capacity": "Kapasitet",
}


def norwegian_errors(exc: ValidationError) -> dict[str, str]:
    """Gjør Pydantic-feil om til én forståelig norsk melding per felt."""
    errors: dict[str, str] = {}
    for err in exc.errors():
        field = str(err["loc"][0]) if err["loc"] else "skjema"
        label = _FIELD_NAMES.get(field, field)
        ctx = err.get("ctx", {})
        kind = err["type"]
        empty = err.get("input") in (None, "")
        if kind == "missing" or empty:
            msg = f"{label} må fylles ut."
        elif field == "member_number":
            msg = "Medlemsnummer må være 4–10 siffer."
        elif kind == "string_too_short":
            msg = f"{label} må ha minst {ctx['min_length']} tegn."
        elif kind == "string_too_long":
            msg = f"{label} kan ha maks {ctx['max_length']} tegn."
        elif kind == "greater_than_equal":
            msg = f"{label} må være minst {ctx['ge']}."
        elif kind == "less_than_equal":
            msg = f"{label} kan være maks {ctx['le']}."
        else:
            msg = f"{label} har en ugyldig verdi."
        errors.setdefault(field, msg)
    return errors
