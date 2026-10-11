"""Starting seasons and laying out their schedule (E132–E134)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots, add_league, register, season_games

from sbm_store import bots, jobs, league_setup, leagues, matches, season_start, seasons
from sbm_store.discipline import STANDARD_FEN
from sbm_store.names import JOBS

LATER = T0 + timedelta(minutes=1)


def start(db, league, now=LATER):
    return season_start.start_due(db, now, random.Random(1))


def test_the_first_season_waits_for_its_release(db):
    league = add_league(db)
    register(db, league, add_bots(db, 3))

    assert start(db, league) == []
    assert league_setup.release(db, league["_id"], T0)
    assert not league_setup.release(db, league["_id"], T0)
    started = start(db, league)

    season = seasons.latest(db, league["_id"])
    assert started == [season["_id"]]
    assert season["status"] == seasons.RUNNING
    assert season["scheduled"]
    assert season["settings"]["league_name"] == "Liga"
    assert season["settings"]["discipline_snapshot"]["name"] == "Blitz"


def test_a_round_robin_with_two_games_per_pairing(db):
    league = add_league(db)
    entrants = add_bots(db, 3)
    register(db, league, entrants)
    league_setup.release(db, league["_id"], T0)
    start(db, league)

    season = seasons.latest(db, league["_id"])
    games = season_games(db, season["_id"])
    assert [entry["bot_id"] for entry in season["tiers"][0]["entries"]] == [
        bot["_id"] for bot in entrants
    ]
    assert len(games) == 6
    pairs = [(game["white"]["bot_id"], game["black"]["bot_id"]) for game in games]
    assert len(set(pairs)) == 6
    assert all(game["type"] == matches.LEAGUE for game in games)
    assert all(game["start_fen"] == STANDARD_FEN for game in games)
    assert all(game["queue"]["priority"] == 50 for game in games)
    assert {game["context"]["round"] for game in games} == {1, 2, 3, 4, 5, 6}
    assert {game["context"]["board"] for game in games} == {1}
    competition = jobs.league_competition(league["_id"])
    queued = list(db[JOBS].find({"payload.match_id": {"$in": [game["_id"] for game in games]}}))
    assert len(queued) == 6
    assert {job["competition"] for job in queued} == {competition}


def test_too_few_bots_keep_the_season_planned(db):
    league = add_league(db, min_participants=3)
    register(db, league, add_bots(db, 2))
    league_setup.release(db, league["_id"], T0)

    assert start(db, league) == []
    assert seasons.latest(db, league["_id"])["status"] == seasons.PLANNED


def test_only_verified_bots_play(db):
    league = add_league(db)
    entrants = add_bots(db, 2)
    retired = add_bots(db, 1, status=bots.RETIRED)
    register(db, league, entrants + retired)
    league_setup.release(db, league["_id"], T0)
    start(db, league)

    entries = seasons.latest(db, league["_id"])["tiers"][0]["entries"]
    assert [entry["bot_id"] for entry in entries] == [bot["_id"] for bot in entrants]


def test_tiers_are_cut_from_the_registrations_in_order(db):
    league = add_league(db, tiers=2, tier_size=2)
    entrants = add_bots(db, 5)
    register(db, league, entrants)
    league_setup.release(db, league["_id"], T0)
    start(db, league)

    season = seasons.latest(db, league["_id"])
    placed = [[entry["bot_id"] for entry in tier["entries"]] for tier in season["tiers"]]
    assert placed == [
        [entrants[0]["_id"], entrants[1]["_id"]],
        [entrants[2]["_id"], entrants[3]["_id"]],
    ]
    assert {game["context"]["tier"] for game in season_games(db, season["_id"])} == {1, 2}


def test_an_archived_league_starts_no_season(db):
    league = add_league(db)
    register(db, league, add_bots(db, 2))
    league_setup.release(db, league["_id"], T0)
    leagues.update(db, league["_id"], {"archived": True}, now=T0)

    assert start(db, league) == []


def test_laying_out_again_adds_only_what_is_missing(db):
    league = add_league(db)
    register(db, league, add_bots(db, 3))
    league_setup.release(db, league["_id"], T0)
    start(db, league)
    season = seasons.latest(db, league["_id"])
    games = season_games(db, season["_id"])
    db[JOBS].delete_one({"payload.match_id": games[0]["_id"]})
    db["seasons"].update_one({"_id": season["_id"]}, {"$set": {"scheduled": False}})

    assert season_start.lay_out_pending(db, LATER) == 1
    assert season_start.lay_out_pending(db, LATER) == 0

    assert len(season_games(db, season["_id"])) == 6
    ids = [game["_id"] for game in games]
    assert db[JOBS].count_documents({"payload.match_id": {"$in": ids}}) == 6
