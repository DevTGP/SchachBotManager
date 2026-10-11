"""The tournament editions of a bot version with its place there (E180)."""

from conftest import T0
from league_world import add_bots
from tournament_world import add_tournament, enter, play_to_the_end, start, stronger

from sbm_store import bot_editions, editions, registrations, tournament_withdrawal, tournaments


def test_a_finished_round_robin_gives_rank_and_points(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, games_per_pairing=1)
    entrants = add_bots(db, 3)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    play_to_the_end(db, edition["_id"], stronger(entrants))

    (found,) = bot_editions.of_bot(db, entrants[1]["_id"])

    assert found.edition["status"] == editions.FINISHED
    assert (found.participants, found.place, found.points, found.withdrawn) == (3, 2, 1, False)


def test_a_running_knockout_gives_no_place_yet(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=1)
    entrants = add_bots(db, 4)
    enter(db, tournament, entrants)
    start(db, tournament)

    (found,) = bot_editions.of_bot(db, entrants[0]["_id"])

    assert found.edition["status"] == editions.RUNNING
    assert (found.participants, found.place, found.points) == (4, None, None)


def test_a_withdrawn_bot_keeps_its_edition_without_a_place(db):
    tournament = add_tournament(db, tournaments.SWISS, rounds=2)
    entrants = add_bots(db, 4)
    enter(db, tournament, entrants)
    start(db, tournament)
    tournament_withdrawal.withdraw(db, entrants[3]["_id"], registrations.DISABLED, T0)

    (found,) = bot_editions.of_bot(db, entrants[3]["_id"])

    assert (found.place, found.withdrawn) == (None, True)


def test_planned_editions_do_not_count(db):
    tournament = add_tournament(db, tournaments.SWISS)
    (waiting,) = add_bots(db, 1)
    enter(db, tournament, [waiting])

    assert bot_editions.of_bot(db, waiting["_id"]) == []
