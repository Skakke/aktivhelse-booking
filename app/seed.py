"""Legger inn testdata hvis databasen er tom.

Timene legges ut fra dagens dato, slik at demoen alltid har kommende timer.
Kjøres automatisk ved oppstart (se entrypoint.sh), eller manuelt:
    python -m app.seed
"""

from datetime import datetime, time, timedelta

from sqlalchemy import select

from app.config import TZ
from app.db import SessionLocal
from app.models import Booking, Department, GroupClass

DEPARTMENTS = ["Sentrum", "Nord", "Sør"]

# (navn, instruktør, avdeling, klokkeslett, varighet, kapasitet)
WEEKLY = [
    ("Spinning", "Kari Nordmann", "Sentrum", time(7, 0), 45, 20),
    ("Yoga", "Ola Hansen", "Nord", time(12, 0), 60, 15),
    ("Styrke", "Lise Berg", "Sør", time(17, 30), 60, 25),
    ("Pilates", "Ingrid Lie", "Sentrum", time(18, 0), 50, 12),
    ("Sirkeltrening", "Ahmed Ali", "Nord", time(19, 0), 45, 18),
]

MEMBERS = [
    ("Anne Johansen", "anne@example.no"), ("Per Olsen", "per@example.no"),
    ("Sara Nilsen", "sara@example.no"), ("Jonas Bakke", "jonas@example.no"),
    ("Maria Dahl", "maria@example.no"), ("Erik Moen", "erik@example.no"),
]


def seed() -> bool:
    with SessionLocal() as db:
        if db.scalar(select(Department.id).limit(1)):
            return False

        deps = {name: Department(name=name) for name in DEPARTMENTS}
        db.add_all(deps.values())

        today = datetime.now(TZ).date()
        classes = []
        for day in range(7):
            for i, (name, instructor, dep, t, dur, cap) in enumerate(WEEKLY):
                if (day + i) % 3 == 2:  # ikke alle timer hver dag
                    continue
                classes.append(GroupClass(
                    name=name, instructor=instructor, department=deps[dep],
                    starts_at=datetime.combine(today + timedelta(days=day), t, TZ),
                    duration_min=dur, capacity=cap,
                ))
        db.add_all(classes)
        db.flush()

        # Én kommende time gjøres helt full for å vise "Fullt" i demoen.
        full = next(c for c in classes if c.name == "Pilates" and c.starts_at > datetime.now(TZ))
        full.capacity = 3

        # Noen påmeldinger på hver time.
        for n, gc in enumerate(classes):
            count = full.capacity if gc is full else n % 4
            for name, email in MEMBERS[:count]:
                db.add(Booking(group_class=gc, name=name, email=email))
        db.commit()
        return True


if __name__ == "__main__":
    print("Testdata lagt inn." if seed() else "Databasen har data fra før, hopper over.")
