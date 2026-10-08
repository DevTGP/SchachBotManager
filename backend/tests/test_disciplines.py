"""GET /disciplines: everyone may read them, archived ones too (E100)."""

from stored_disciplines import store_discipline


def test_list_by_name_with_archived_ones(client, db):
    store_discipline(db, "rapid")
    store_discipline(db, "Blitz", archived=True)

    response = client.get("/api/v1/disciplines")

    assert response.status_code == 200
    items = response.json["items"]
    assert [(item["name"], item["archived"]) for item in items] == [
        ("Blitz", True),
        ("rapid", False),
    ]


def test_one_discipline(client, db):
    discipline = store_discipline(db, "Bullet")

    response = client.get(f"/api/v1/disciplines/{discipline['_id']}")

    assert response.status_code == 200
    assert response.json["id"] == str(discipline["_id"])
    assert response.json["initial_time_ms"] == 60_000


def test_unknown_or_invalid_ids(client):
    assert client.get("/api/v1/disciplines/0123456789abcdef01234567").status_code == 404
    response = client.get("/api/v1/disciplines/nope")
    assert (response.status_code, response.json["field"]) == (400, "discipline_id")
