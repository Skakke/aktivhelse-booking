"""Tester nettsidene og API-et gjennom HTTP, slik en bruker ville brukt dem."""

from datetime import timedelta


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_schedule_page_lists_classes(client, make_class):
    make_class(name="Spinning", room="Sykkelsal")
    r = client.get("/")
    assert r.status_code == 200
    assert "Spinning" in r.text
    assert "Sykkelsal" in r.text
    assert "10 av 10 ledig" in r.text


def test_booking_form_shows_norwegian_errors(client, make_class):
    gc = make_class()
    r = client.post(f"/classes/{gc.id}/book", data={"name": "", "member_number": "12ab"})
    assert "Navn må fylles ut." in r.text
    assert "Medlemsnummer må være 4–10 siffer." in r.text


def test_booking_via_web_triggers_list_refresh(client, make_class):
    gc = make_class()
    r = client.post(f"/classes/{gc.id}/book", data={"name": "Anne", "member_number": "100001"})
    assert "Du er påmeldt" in r.text
    assert r.headers["HX-Trigger"] == "classesChanged"


def test_my_bookings_hides_cancel_after_deadline(client, make_class):
    early = make_class(name="Yoga", starts_in=timedelta(days=1))
    late = make_class(name="Spinning", starts_in=timedelta(minutes=30))
    for gc in (early, late):
        client.post(f"/classes/{gc.id}/book", data={"name": "Anne", "member_number": "100001"})
    r = client.get("/mine", params={"member": "100001"})
    assert r.text.count(">Meld av</button>") == 1
    assert "Avmeldingsfristen er passert" in r.text


def test_api_full_class_returns_409(client, make_class):
    gc = make_class(capacity=1)
    ok = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Anne", "member_number": "100001"})
    assert ok.status_code == 201
    full = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Per", "member_number": "100002"})
    assert full.status_code == 409
    assert full.json()["detail"] == "Timen er dessverre full."


def test_api_cancel(client, make_class):
    gc = make_class()
    b = client.post(f"/api/classes/{gc.id}/bookings", json={"name": "Anne", "member_number": "100001"}).json()
    r = client.delete(f"/api/bookings/{b['id']}", params={"member_number": "100001"})
    assert r.status_code == 204
    assert client.get(f"/api/classes/{gc.id}").json()["booked"] == 0


def test_admin_create_class_validates(client, department):
    r = client.post("/admin/classes", data={
        "name": "", "instructor": "Kari", "department_id": str(department.id), "room": "",
        "starts_at": "2030-01-01T10:00", "duration_min": "60", "capacity": "0",
    })
    assert r.status_code == 422
    assert "Navn må fylles ut." in r.text
    assert "Sal må fylles ut." in r.text
    assert "Kapasitet må være minst 1." in r.text


def test_admin_can_add_participant(client, make_class):
    gc = make_class(capacity=1)
    r = client.post(f"/admin/classes/{gc.id}/bookings", data={"name": "Per", "member_number": "100002"})
    assert "100002" in r.text
    r = client.post(f"/admin/classes/{gc.id}/bookings", data={"name": "Sara", "member_number": "100003"})
    assert "Timen er dessverre full." in r.text
