"""A bot leaving its leagues mid-season (E136)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots, add_league, register, season_games

from sbm_store import (
    jobs,
    league_setup,
    league_withdrawal,
    matches,
    registrations,
    season_start,
    seasons,
)
from sbm_store.names import JOBS, MATCHES

LATER = T0 + timedelta(minutes=1)
LEFT = T0 + timedelta(minutes=5)


def running_season(db, entrants, name="Liga"):
    league = add_league(db, name)
    register(db, league, entrants)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, LATER, random.Random(1))
    return league, seasons.latest(db, league["_id"])


def games_of(db, season, bot):
    return [
        game
        for game in season_games(db, season["_id"])
        if bot["_id"] in (game["white"]["bot_id"], game["black"]["bot_id"])
    ]


def test_waiting_games_end_as_forfeits_and_a_running_one_goes_on(db):
    entrants = add_bots(db, 3)
    league, season = running_season(db, entrants)
    leaving = entrants[0]
    own = games_of(db, season, leaving)
    db[MATCHES].update_one({"_id": own[0]["_id"]}, {"$set": {"status": matches.RUNNING}})

    forfeited = league_withdrawal.withdraw(db, leaving["_id"], registrations.RETIRED, LEFT)

    assert forfeited == len(own) - 1
    assert seasons.get(db, season["_id"])["withdrawn"] == [leaving["_id"]]
    assert registrations.get_active(db, league["_id"], leaving["_id"]) is None
    assert db[MATCHES].find_one({"_id": own[0]["_id"]})["status"] == matches.RUNNING
    for game in own[1:]:
        ended = db[MATCHES].find_one({"_id": game["_id"]})
        lost_with_white = ended["white"]["bot_id"] == leaving["_id"]
        assert ended["status"] == matches.FINISHED
        assert ended["termination"] == matches.FORFEIT
        assert ended["result"] == ("0-1" if lost_with_white else "1-0")
        assert not ended["rated"]
        assert db[JOBS].find_one({"payload.match_id": game["_id"]})["status"] == jobs.CANCELLED
    own_ids = {game["_id"] for game in own}
    others = [game for game in season_games(db, season["_id"]) if game["_id"] not in own_ids]
    assert others
    assert all(game["status"] == matches.QUEUED for game in others)


def test_the_sweep_ends_games_a_crash_left_waiting(db):
    entrants = add_bots(db, 2)
    _, season = running_season(db, entrants)
    seasons.add_withdrawn(db, season["_id"], entrants[1]["_id"])

    assert league_withdrawal.sweep(db, LEFT) == 2
    assert league_withdrawal.sweep(db, LEFT) == 0


def test_leaving_one_league_keeps_the_others(db):
    entrants = add_bots(db, 2)
    first, _ = running_season(db, entrants, "Erste")
    second, season = running_season(db, entrants, "Zweite")

    league_withdrawal.withdraw(
        db, entrants[0]["_id"], registrations.DEREGISTERED, LEFT, league_id=first["_id"]
    )

    assert registrations.get_active(db, second["_id"], entrants[0]["_id"]) is not None
    assert seasons.get(db, season["_id"])["withdrawn"] == []
