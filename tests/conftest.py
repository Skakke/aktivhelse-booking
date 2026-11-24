"""Testoppsett: egen testdatabase som tømmes mellom hver test."""

import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import TZ
from app.db import Base, get_db
from app.main import app
from app.models import Department, GroupClass

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://booking:booking@localhost:5432/booking_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE bookings, group_classes, departments RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    with TestSession() as session:
        yield session


@pytest.fixture
def client():
    def _get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def department(db):
    dep = Department(name="Sentrum")
    db.add(dep)
    db.commit()
    return dep


@pytest.fixture
def make_class(db, department):
    def _make(capacity=10, starts_in=timedelta(days=1), name="Spinning", room="Sal 1"):
        gc = GroupClass(
            name=name, instructor="Kari", department_id=department.id, room=room,
            starts_at=datetime.now(TZ) + starts_in, duration_min=45, capacity=capacity,
        )
        db.add(gc)
        db.commit()
        return gc

    return _make
