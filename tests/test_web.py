"""Tester nettsidene og API-et gjennom HTTP, slik en bruker ville brukt dem."""


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_schedule_page_lists_classes(client, make_class):
    make_class(name="Spinning")
    r = client.get("/")
    assert r.status_code == 200
    assert "Spinning" in r.text
    assert "10 av 10 ledig" in r.text


def test_booking_form_shows_norwegian_errors(client, make_class):
    gc = make_class()
    r = client.post(f"/classes/{gc.id}/book", data={"name": "", "email": "feil"})
    assert "Navn må fylles ut." in r.text
    assert "Skriv inn en gyldig e-postadresse." in r.text


def test_booking_via_web_triggers_list_refresh(client, make_class):
    gc = make_class()
    r = client.post(f"/classes/{gc.id}/book", data={"name": "Anne", "email": "anne@example.no"})
    assert "Du er påmeldt" in r.text
    assert r.headers["HX-Trigger"] == "classesChanged"


def test_api_full_class_returns_409(client, make_class):
    gc = make_class(capacity=1)
    ok = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Anne", "email": "anne@example.no"})
    assert ok.status_code == 201
    full = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Per", "email": "per@example.no"})
    assert full.status_code == 409
    assert full.json()["detail"] == "Timen er dessverre full."


def test_api_cancel(client, make_class):
    gc = make_class()
    b = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Anne", "email": "anne@example.no"}).json()
    assert client.delete(f"/api/bookings/{b['id']}", params={"email": "anne@example.no"}).status_code == 204
    assert client.get(f"/api/classes/{gc.id}").json()["booked"] == 0


def test_admin_create_class_validates(client, department):
    r = client.post("/admin/classes", data={
        "name": "", "instructor": "Kari", "department_id": str(department.id),
        "starts_at": "2030-01-01T10:00", "duration_min": "60", "capacity": "0",
    })
    assert r.status_code == 422
    assert "Navn på" in r.text or "Navn må fylles ut." in r.text
    assert "Kapasitet må være minst 1." in r.text
