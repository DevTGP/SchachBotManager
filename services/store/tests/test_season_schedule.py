"""The schedule of a tier by rounds and boards (E138)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots, add_league, register

from sbm_store import league_setup, matches, season_schedule, season_start, seasons
from sbm_store.names import MATCHES


def start(db, entrants, **settings) -> dict:
    league = add_league(db, **settings)
    register(db, league, entrants)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, T0 + timedelta(minutes=1), random.Random(1))
    return seasons.latest(db, league["_id"])


def test_an_odd_tier_has_one_bye_per_round(db):
    entrants = add_bots(db, 3)
    season = start(db, entrants, games_per_pairing=1)

    rounds = season_schedule.rounds(db, season, 1)

    assert [each.number for each in rounds] == [1, 2, 3]
    for each in rounds:
        (game,) = each.games
        assert game["context"]["board"] == 1
        assert each.bye["bot_id"] not in {game["white"]["bot_id"], game["black"]["bot_id"]}
    assert {each.bye["bot_id"] for each in rounds} == {bot["_id"] for bot in entrants}


def test_an_even_tier_plays_on_boards_in_order(db):
    season = start(db, add_bots(db, 4), games_per_pairing=1)
    first = season_schedule.rounds(db, season, 1)[0].games[0]
    db[MATCHES].update_one(
        {"_id": first["_id"]},
        {"$set": {"status": matches.FINISHED, "result": "1-0", "termination": "checkmate"}},
    )

    rounds = season_schedule.rounds(db, season, 1)

    assert len(rounds) == 3
    assert all(each.bye is None for each in rounds)
    assert all([game["context"]["board"] for game in each.games] == [1, 2] for each in rounds)
    played = rounds[0].games[0]
    assert (played["status"], played["result"], played["termination"]) == (
        matches.FINISHED,
        "1-0",
        "checkmate",
    )
    assert rounds[0].games[1]["status"] == matches.QUEUED


def test_no_schedule_without_the_tier(db):
    season = start(db, add_bots(db, 2))
    planned = seasons.latest(db, add_league(db, "Andere")["_id"])

    assert season_schedule.rounds(db, season, 2) is None
    assert season_schedule.rounds(db, planned, 1) is None
