"""Creating tournaments, starting an edition by hand and following a new calendar (E171, E172)."""

from datetime import timedelta

from conftest import T0
from tournament_world import add_tournament

from sbm_store import editions, recurrence, tournament_setup, tournaments


def test_without_a_calendar_the_first_edition_waits_for_an_admin(db):
    tournament = add_tournament(db, tournaments.SWISS)

    (first,) = editions.of_tournament(db, tournament["_id"])
    assert (first["number"], first["status"], first["starts_after"]) == (1, editions.PLANNED, None)
    assert tournament_setup.start(db, tournament["_id"], T0)
    assert editions.get(db, first["_id"])["starts_after"] == T0
    assert not tournament_setup.start(db, tournament["_id"], T0)


def test_with_a_calendar_the_first_edition_waits_for_its_date(db):
    calendar = recurrence.new_recurrence(T0 + timedelta(hours=5), 24)
    tournament = add_tournament(db, tournaments.KNOCKOUT, recurrence=calendar)

    first = editions.latest(db, tournament["_id"])
    assert first["starts_after"] == T0 + timedelta(hours=5)
    # Starting by hand brings the date forward.
    assert tournament_setup.start(db, tournament["_id"], T0)
    assert editions.get(db, first["_id"])["starts_after"] == T0


def test_a_taken_name_is_refused_regardless_of_case(db):
    add_tournament(db, tournaments.ROUND_ROBIN, name="Pokal")
    twin = tournaments.new_tournament(
        {"name": "POKAL", "discipline_id": None, "format": tournaments.SWISS},
        created_by=None,
        now=T0,
    )

    assert not tournament_setup.create(db, twin, T0)
    assert editions.of_tournament(db, twin["_id"]) == []


def test_starting_a_tournament_without_an_edition_adds_the_first(db):
    tournament = add_tournament(db, tournaments.SWISS)
    db["editions"].delete_many({"tournament_id": tournament["_id"]})

    assert tournament_setup.start(db, tournament["_id"], T0)
    first = editions.latest(db, tournament["_id"])
    assert (first["number"], first["starts_after"]) == (1, T0)


def test_a_new_calendar_moves_the_planned_edition(db):
    tournament = add_tournament(db, tournaments.SWISS)
    calendar = recurrence.new_recurrence(T0 - timedelta(hours=1), 6)
    changed = tournaments.update(db, tournament["_id"], {"recurrence": calendar}, now=T0)

    tournament_setup.follow_calendar(db, changed, T0)
    assert editions.latest(db, tournament["_id"])["starts_after"] == T0 + timedelta(hours=5)

    cleared = tournaments.update(db, tournament["_id"], {"recurrence": None}, now=T0)
    tournament_setup.follow_calendar(db, cleared, T0)
    assert editions.latest(db, tournament["_id"])["starts_after"] is None
