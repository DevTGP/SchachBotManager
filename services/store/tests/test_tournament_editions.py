"""Starting, playing and finishing tournament editions in the three formats (E173–E178)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots
from tournament_world import (
    add_tournament,
    draws,
    edition_matches,
    enter,
    finish_waiting,
    play_to_the_end,
    start,
    stronger,
)

from sbm_store import (
    disciplines,
    edition_progress,
    edition_start,
    editions,
    jobs,
    knockout_bracket,
    matches,
    recurrence,
    tournament_setup,
    tournaments,
)
from sbm_store.discipline import Discipline
from sbm_store.migrate import migrate
from sbm_store.names import BOTS, JOBS


def rated(db, entrants: list[dict], tournament: dict) -> None:
    """Gives the bots falling ratings in the tournament's discipline, the first the highest."""
    key = str(tournament["discipline_id"])
    for number, bot in enumerate(entrants):
        value = {"value": 1600 - 10 * number, "games": 5, "seq": 1}
        db[BOTS].update_one({"_id": bot["_id"]}, {"$set": {f"ratings.{key}": value}})


def test_an_edition_waits_for_enough_bots_and_an_admin(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, min_participants=3)
    enter(db, tournament, add_bots(db, 2))

    assert edition_start.start_due(db, T0, random.Random(1)) == []
    assert tournament_setup.start(db, tournament["_id"], T0)
    assert edition_start.start_due(db, T0, random.Random(1)) == []

    enter(db, tournament, add_bots(db, 1))
    assert len(edition_start.start_due(db, T0, random.Random(1))) == 1


def test_participants_are_seeded_by_rating_and_unverified_bots_stay_out(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN)
    entrants = add_bots(db, 3)
    (pending,) = add_bots(db, 1, status="pending")
    rated(db, list(reversed(entrants)), tournament)
    enter(db, tournament, [*entrants, pending])

    edition = start(db, tournament)

    assert [entry["bot_id"] for entry in edition["participants"]] == [
        bot["_id"] for bot in reversed(entrants)
    ]
    assert [entry["seed"] for entry in edition["participants"]] == [1, 2, 3]
    assert edition["settings"]["tournament_name"] == "Pokal"
    assert edition["settings"]["discipline_snapshot"]["name"] == "Blitz"
    assert edition["settings"]["tiebreak_discipline_snapshot"] is None


def test_a_round_robin_edition_lays_out_all_games_and_finishes(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, games_per_pairing=2)
    entrants = add_bots(db, 3)
    rated(db, entrants, tournament)
    enter(db, tournament, entrants)

    edition = start(db, tournament)

    games = edition_matches(db, edition["_id"])
    assert len(games) == 6
    assert edition["scheduled"]
    assert {game["type"] for game in games} == {matches.TOURNAMENT}
    assert {game["queue"]["priority"] for game in games} == {40}
    assert games[0]["context"]["tournament_id"] == tournament["_id"]
    assert games[0]["context"]["edition_number"] == 1
    competition = jobs.tournament_competition(tournament["_id"])
    # One game per round, only the first round is queued (E189).
    assert db[JOBS].count_documents({"competition": competition}) == 1

    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    table = finished["final"]["table"]
    assert [row["bot"]["bot_id"] for row in table] == [bot["_id"] for bot in entrants]
    assert [row["points"] for row in table] == [4, 2, 0]
    assert finished["winner"]["bot_id"] == entrants[0]["_id"]
    following = editions.latest(db, tournament["_id"])
    assert (following["number"], following["status"]) == (2, editions.PLANNED)
    assert following["starts_after"] is None


def test_the_next_edition_follows_the_calendar_and_starts_at_once_if_its_date_passed(db):
    calendar = recurrence.new_recurrence(T0, 1)
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, recurrence=calendar)
    entrants = add_bots(db, 2)
    enter(db, tournament, entrants)
    (first,) = edition_start.start_due(db, T0, random.Random(1))

    late = T0 + timedelta(hours=5)
    play_to_the_end(db, first, stronger(entrants), now=late)

    following = editions.latest(db, tournament["_id"])
    assert following["starts_after"] == T0 + timedelta(hours=1)
    assert edition_start.start_due(db, late, random.Random(2)) == [following["_id"]]


def test_the_swiss_system_pairs_round_after_round_with_one_bye_each(db):
    tournament = add_tournament(db, tournaments.SWISS, rounds=3)
    entrants = add_bots(db, 5)
    rated(db, entrants, tournament)
    enter(db, tournament, entrants)

    edition = start(db, tournament)
    assert edition["rounds"] == []
    edition_progress.advance_running(db, T0, random.Random(1))
    edition = editions.get(db, edition["_id"])
    assert edition["round"] == 1
    assert len(edition_matches(db, edition["_id"])) == 2
    # Nothing new while round 1 runs.
    edition_progress.advance_running(db, T0, random.Random(1))
    assert len(edition_matches(db, edition["_id"])) == 2

    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    assert finished["round"] == 3
    byes = [planned["bye"] for planned in finished["rounds"]]
    assert len(set(byes)) == 3
    met = [
        frozenset((pairing["white"], pairing["black"]))
        for planned in finished["rounds"]
        for pairing in planned["pairings"]
    ]
    assert len(met) == len(set(met)) == 6
    table = finished["final"]["table"]
    assert sum(row["points"] for row in table) == 6 + 3
    assert table[0]["bot"]["bot_id"] == entrants[0]["_id"]
    assert sum(row["byes"] for row in table) == 3


def test_knockout_seeds_play_their_duels_and_the_winners_move_on(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=2)
    entrants = add_bots(db, 3)
    rated(db, entrants, tournament)
    enter(db, tournament, entrants)

    edition = start(db, tournament)
    assert edition["bracket_size"] == 4
    assert [duel["decided_by"] for duel in edition["duels"]] == [knockout_bracket.BYE, None]

    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    places = finished["final"]["placements"]
    assert [(each["bot"]["bot_id"], each["place"]) for each in places] == [
        (entrants[0]["_id"], 1),
        (entrants[1]["_id"], 2),
        (entrants[2]["_id"], 3),
    ]
    assert finished["winner"]["bot_id"] == entrants[0]["_id"]
    final = finished["duels"][-1]
    assert (final["round"], final["decided_by"]) == (2, knockout_bracket.GAMES)
    assert [game["phase"] for game in final["games"]] == ["regular", "regular"]


def test_a_drawn_duel_goes_to_tiebreak_games_and_then_armageddon(db):
    migrate(db)
    bullet = disciplines.new_discipline(
        Discipline("Bullet", initial_time_ms=30_000, increment_ms=0), created_by=None, now=T0
    )
    assert disciplines.insert(db, bullet)
    tournament = add_tournament(
        db,
        tournaments.KNOCKOUT,
        games_per_pairing=2,
        tiebreak_pairs=1,
        tiebreak_discipline_id=bullet["_id"],
    )
    entrants = add_bots(db, 2)
    enter(db, tournament, entrants)

    finished = play_to_the_end(db, start(db, tournament)["_id"], draws)

    (duel,) = finished["duels"]
    assert duel["decided_by"] == knockout_bracket.ARMAGEDDON
    phases = [game["phase"] for game in duel["games"]]
    assert phases == ["regular", "regular", "tiebreak", "tiebreak", "armageddon"]
    armageddon = duel["games"][-1]
    assert duel["winner"] == armageddon["black"]
    games = {game["_id"]: game for game in edition_matches(db, finished["_id"])}
    names = [games[game["match_id"]]["discipline_snapshot"]["name"] for game in duel["games"]]
    assert names == ["Blitz", "Blitz", "Bullet", "Bullet", "Bullet"]


def test_an_aborted_duel_game_is_played_again(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=1, tiebreak_pairs=0)
    entrants = add_bots(db, 2)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    edition_progress.advance_running(db, T0, random.Random(1))
    (first,) = edition_matches(db, edition["_id"], matches.QUEUED)
    assert matches.abort(db, first["_id"], "engine crashed", T0)

    edition_progress.advance_running(db, T0, random.Random(1))

    (again,) = edition_matches(db, edition["_id"], matches.QUEUED)
    assert again["_id"] != first["_id"]
    assert again["white"]["bot_id"] == first["white"]["bot_id"]
    assert finish_waiting(db, edition["_id"], stronger(entrants)) == 1
