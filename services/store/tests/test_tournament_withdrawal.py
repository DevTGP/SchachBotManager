"""Bots leaving their tournaments (E179)."""

import random

from conftest import T0
from league_world import add_bots, add_league, register
from tournament_world import (
    add_tournament,
    edition_matches,
    enter,
    finish_waiting,
    play_to_the_end,
    start,
    stronger,
)

from sbm_store import (
    bot_deletion,
    edition_progress,
    editions,
    knockout_bracket,
    league_setup,
    matches,
    registrations,
    season_start,
    tournament_withdrawal,
    tournaments,
    withdrawal,
)


def test_leaving_forfeits_the_waiting_games_and_keeps_the_bot_without_a_rank(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN)
    entrants = add_bots(db, 3)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    leaving = entrants[2]["_id"]

    forfeited = tournament_withdrawal.withdraw(db, leaving, registrations.DEREGISTERED, T0)

    assert forfeited == 4
    assert registrations.active_of_bot(db, leaving, target_type=registrations.TOURNAMENT) == []
    lost = [
        game
        for game in edition_matches(db, edition["_id"])
        if leaving in (game["white"]["bot_id"], game["black"]["bot_id"])
    ]
    assert {game["termination"] for game in lost} == {matches.FORFEIT}
    assert {game["termination_detail"] for game in lost} == {matches.LEFT_TOURNAMENT}
    finished = play_to_the_end(db, edition["_id"], stronger(entrants))
    last = finished["final"]["table"][-1]
    assert (last["bot"]["bot_id"], last["rank"], last["withdrawn"]) == (leaving, None, True)


def test_a_withdrawn_bot_loses_its_duel_at_once(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=2)
    entrants = add_bots(db, 2)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    edition_progress.advance_running(db, T0, random.Random(1))

    tournament_withdrawal.withdraw(
        db, entrants[0]["_id"], registrations.DEREGISTERED, T0, tournament_id=tournament["_id"]
    )
    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    (duel,) = finished["duels"]
    assert (duel["decided_by"], duel["winner"]) == (
        knockout_bracket.WITHDRAWAL,
        entrants[1]["_id"],
    )
    places = finished["final"]["placements"]
    assert [(each["bot"]["bot_id"], each["place"]) for each in places] == [
        (entrants[1]["_id"], 1),
        (entrants[0]["_id"], None),
    ]


def test_a_winner_who_leaves_does_not_move_on(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=1, tiebreak_pairs=0)
    entrants = add_bots(db, 4)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    edition_progress.advance_running(db, T0, random.Random(1))
    first_round = edition_matches(db, edition["_id"], matches.QUEUED)
    assert len(first_round) == 2
    for game in first_round:
        matches_won = "1-0" if game["context"]["board"] == 1 else "0-1"
        db["matches"].update_one(
            {"_id": game["_id"]},
            {"$set": {"status": matches.FINISHED, "result": matches_won, "termination": "x"}},
        )
    edition_progress.advance_running(db, T0, random.Random(1))
    winner = editions.get(db, edition["_id"])["duels"][0]["winner"]

    tournament_withdrawal.withdraw(db, winner, registrations.RETIRED, T0)
    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    final = finished["duels"][-1]
    assert final["round"] == 2
    assert final["decided_by"] == knockout_bracket.WITHDRAWAL
    assert final["winner"] != winner
    assert finished["winner"]["bot_id"] == final["winner"]


def test_withdrawing_everywhere_leaves_leagues_and_tournaments(db):
    entrants = add_bots(db, 3)
    league = add_league(db)
    register(db, league, entrants)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, T0, random.Random(1))
    tournament = add_tournament(db, tournaments.ROUND_ROBIN)
    enter(db, tournament, entrants)
    start(db, tournament)

    forfeited = withdrawal.withdraw_everywhere(db, entrants[0]["_id"], registrations.DISABLED, T0)

    assert forfeited == 8
    assert registrations.active_of_bot(db, entrants[0]["_id"]) == []
    assert (
        registrations.active_of_bot(db, entrants[0]["_id"], target_type=registrations.TOURNAMENT)
        == []
    )


def test_the_games_of_a_deleted_bot_do_not_come_back(db):
    tournament = add_tournament(db, tournaments.SWISS, rounds=3)
    entrants = add_bots(db, 4)
    enter(db, tournament, entrants)
    edition = start(db, tournament)
    edition_progress.advance_running(db, T0, random.Random(1))
    finish_waiting(db, edition["_id"], stronger(entrants))
    gone = entrants[3]["_id"]

    assert bot_deletion.delete_bot(db, gone, T0) is not None
    withdrawal.withdraw_everywhere(db, gone, registrations.DELETED, T0)
    finished = play_to_the_end(db, edition["_id"], stronger(entrants))

    played = edition_matches(db, finished["_id"])
    assert all(gone not in (game["white"]["bot_id"], game["black"]["bot_id"]) for game in played)
    assert finished["round"] == 3
