"""POST and PATCH /admin/tournaments and POST /admin/tournaments/{tournament_id}/start (E171,
E172, E180)."""

import pytest
from bson import ObjectId
from sbm_store import editions, tournaments
from sbm_store.names import AUDIT_LOG
from stored_tournaments import store_tournament

from accounts import CSRF
from stored_disciplines import store_discipline
from stored_games import NOW

CALENDAR = {"first_start": "2026-11-01T18:00:00Z", "interval_hours": 168}


def create(client, discipline: dict, **body):
    request = {
        "name": "Pokal",
        "discipline_id": str(discipline["_id"]),
        "format": "swiss",
    } | body
    return client.post("/api/v1/admin/tournaments", json=request, headers=CSRF)


def update(client, tournament_id, **body):
    return client.patch(f"/api/v1/admin/tournaments/{tournament_id}", json=body, headers=CSRF)


def start(client, tournament_id):
    return client.post(f"/api/v1/admin/tournaments/{tournament_id}/start", headers=CSRF)


def test_create_with_defaults_a_planned_edition_and_an_audit_entry(admin, db):
    blitz = store_discipline(db, "Blitz")

    response = create(admin, blitz, name="  Pokal  ", rounds=7)

    assert response.status_code == 201
    created = response.json
    assert (created["name"], created["discipline_name"], created["format"]) == (
        "Pokal",
        "Blitz",
        "swiss",
    )
    assert (created["rounds"], created["games_per_pairing"], created["priority"]) == (7, 2, 40)
    assert created["tiebreaks"] == ["buchholz", "sonneborn_berger", "wins"]
    assert (created["recurrence"], created["tiebreak_discipline_name"]) == (None, None)
    assert created["edition"]["status"] == "planned"
    assert created["edition"]["starts_after"] is None
    entry = db[AUDIT_LOG].find_one({"action": "tournament.create"})
    assert entry["target"] == ObjectId(created["id"])


def test_a_calendar_sets_the_start_of_the_first_edition(admin, db):
    blitz = store_discipline(db, "Blitz")

    created = create(admin, blitz, recurrence=CALENDAR).json

    assert created["recurrence"] == {
        "first_start": "2026-11-01T18:00:00.000Z",
        "interval_hours": 168,
    }
    assert created["edition"]["starts_after"] == "2026-11-01T18:00:00.000Z"


def test_names_are_unique_regardless_of_case(admin, db):
    blitz = store_discipline(db, "Blitz")
    create(admin, blitz)

    response = create(admin, blitz, name="POKAL", format="knockout")

    assert (response.status_code, response.json["code"]) == (409, "name_taken")


@pytest.mark.parametrize(
    "body",
    [
        {"format": "league"},
        {"rounds": 0},
        {"games_per_pairing": 11},
        {"tiebreak_pairs": 6},
        {"min_participants": 1},
        {"tiebreaks": ["wins", "wins"]},
        {"tiebreaks": ["coin"]},
        {"recurrence": {"first_start": "2026-11-01T18:00:00", "interval_hours": 24}},
        {"recurrence": {"first_start": "2026-11-01T18:00:00Z", "interval_hours": 0}},
        {"recurrence": {"first_start": "2026-11-01T18:00:00Z"}},
        {"name": "x" * 41},
        {"colour": "blue"},
    ],
)
def test_invalid_settings_are_refused(admin, db, body):
    blitz = store_discipline(db, "Blitz")

    response = create(admin, blitz, **body)

    assert (response.status_code, response.json["code"]) == (400, "invalid_parameter")


def test_a_tiebreak_discipline_must_be_in_use(admin, db):
    blitz = store_discipline(db, "Blitz")
    old = store_discipline(db, "Alt", archived=True)
    bullet = store_discipline(db, "Bullet", initial_time_ms=30_000)

    refused = create(admin, blitz, format="knockout", tiebreak_discipline_id=str(old["_id"]))
    created = create(admin, blitz, format="knockout", tiebreak_discipline_id=str(bullet["_id"]))

    assert refused.json["field"] == "tiebreak_discipline_id"
    assert created.json["tiebreak_discipline_name"] == "Bullet"


def test_update_changes_settings_but_not_the_format(admin, db):
    tournament = store_tournament(db)
    store_tournament(db, "Andere")

    changed = update(admin, tournament["_id"], name="Neu", rounds=3, archived=True)

    assert changed.status_code == 200
    assert (changed.json["name"], changed.json["rounds"], changed.json["archived"]) == (
        "Neu",
        3,
        True,
    )
    assert db[AUDIT_LOG].find_one({"action": "tournament.update"})["details"]["name"] == "Neu"
    assert update(admin, tournament["_id"], format="swiss").json["code"] == "invalid_parameter"
    assert update(admin, tournament["_id"], name="andere").json["code"] == "name_taken"
    assert update(admin, tournament["_id"]).json["code"] == "invalid_parameter"
    assert update(admin, ObjectId()).status_code == 404


def test_a_new_calendar_moves_the_waiting_edition(admin, db):
    tournament = store_tournament(db)

    update(admin, tournament["_id"], recurrence=CALENDAR)
    waiting = editions.latest(db, tournament["_id"])
    update(admin, tournament["_id"], recurrence=None)
    cleared = editions.latest(db, tournament["_id"])

    assert waiting["starts_after"].isoformat() == "2026-11-01T18:00:00+00:00"
    assert cleared["starts_after"] is None


def test_start_releases_the_waiting_edition_once(admin, db, clock):
    tournament = store_tournament(db)

    first = start(admin, tournament["_id"])
    again = start(admin, tournament["_id"])

    assert first.status_code == 200
    assert editions.latest(db, tournament["_id"])["starts_after"] == clock.now()
    assert (again.status_code, again.json["code"]) == (409, "tournament_state")
    assert db[AUDIT_LOG].count_documents({"action": "tournament.start"}) == 1


def test_an_archived_tournament_does_not_start(admin, db):
    tournament = store_tournament(db)
    tournaments.update(db, tournament["_id"], {"archived": True}, now=NOW)

    response = start(admin, tournament["_id"])

    assert (response.status_code, response.json["code"]) == (409, "tournament_state")


def test_only_admins_manage_tournaments(login, db):
    coder, _ = login()
    blitz = store_discipline(db, "Blitz")
    tournament = store_tournament(db)

    assert create(coder, blitz).status_code == 403
    assert update(coder, tournament["_id"], name="X").status_code == 403
    assert start(coder, tournament["_id"]).status_code == 403
