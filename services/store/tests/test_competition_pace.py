"""League and round robin games come round by round: nobody gets more than one game ahead (E187)."""

import random
from datetime import timedelta

from bson import ObjectId
from conftest import T0
from league_world import (
    add_accounts,
    add_bots,
    add_league,
    register,
    register_accounts,
    season_games,
)
from tournament_world import add_tournament, edition_matches, enter, start

from sbm_store import (
    competition_pace,
    competition_readiness,
    edition_progress,
    jobs,
    league_setup,
    league_withdrawal,
    matches,
    registrations,
    season_start,
    seasons,
    tournaments,
)
from sbm_store.names import JOBS, MATCHES

LATER = T0 + timedelta(minutes=1)


def running_season(db, entrants, accounts=(), **settings) -> dict:
    league = add_league(db, **settings)
    register(db, league, entrants)
    register_accounts(db, league, list(accounts))
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, LATER, random.Random(1))
    return seasons.latest(db, league["_id"])


def with_job(db, games: list[dict]) -> list[dict]:
    """The games among games that have a match job, as (tier or None, round, board)."""
    ids = set(db[JOBS].distinct("payload.match_id", {"type": jobs.MATCH}))
    return sorted(
        (game["context"].get("tier"), game["context"]["round"], game["context"]["board"])
        for game in games
        if game["_id"] in ids
    )


def end(db, game: dict) -> None:
    db[MATCHES].update_one(
        {"_id": game["_id"]},
        {"$set": {"status": matches.FINISHED, "result": "1-0", "termination": "checkmate"}},
    )
    db[JOBS].update_one({"payload.match_id": game["_id"]}, {"$set": {"status": jobs.DONE}})


def of_round(games: list[dict], number: int) -> list[dict]:
    return [game for game in games if game["context"]["round"] == number]


def test_a_season_queues_only_the_first_round_of_each_tier(db):
    season = running_season(db, add_bots(db, 5), tiers=2, tier_size=3)

    games = season_games(db, season["_id"])
    assert with_job(db, games) == [(1, 1, 1), (2, 1, 1)]
    assert season_start.hand_out(db, LATER) == 0


def test_the_next_round_follows_once_every_game_of_the_round_has_ended(db):
    season = running_season(db, add_bots(db, 4), games_per_pairing=1)
    games = season_games(db, season["_id"])
    first, second = of_round(games, 1)
    assert with_job(db, games) == [(1, 1, 1), (1, 1, 2)]

    end(db, first)
    db[MATCHES].update_one({"_id": second["_id"]}, {"$set": {"status": matches.RUNNING}})
    assert season_start.hand_out(db, LATER) == 0

    end(db, second)
    assert season_start.hand_out(db, LATER) == 2
    assert with_job(db, games) == [(1, 1, 1), (1, 1, 2), (1, 2, 1), (1, 2, 2)]


def test_forfeits_of_a_withdrawn_bot_end_the_round(db):
    entrants = add_bots(db, 3)
    season = running_season(db, entrants, games_per_pairing=1)
    games = season_games(db, season["_id"])
    (opening,) = of_round(games, 1)
    leaving = opening["white"]["bot_id"]

    league_withdrawal.withdraw(db, leaving, registrations.RETIRED, LATER)

    assert season_start.hand_out(db, LATER) == 1
    (current,) = of_round(games, 2)
    assert with_job(db, games) == [(1, 1, 1), (1, 2, 1)]
    assert leaving not in (current["white"]["bot_id"], current["black"]["bot_id"])


def test_an_account_and_the_bots_wait_for_each_other(db):
    (account,) = add_accounts(db, 1)
    season = running_season(db, add_bots(db, 3), [account], games_per_pairing=1)
    games = season_games(db, season["_id"])
    mine = [game for game in games if competition_readiness.color_of(game, account["_id"])]
    (own_first,) = of_round(mine, 1)
    (bots_first,) = [game for game in of_round(games, 1) if game not in mine]
    assert with_job(db, games) == [(1, 1, bots_first["context"]["board"])]

    assert competition_readiness.release(db, LATER) == [own_first["_id"]]
    end(db, bots_first)
    assert season_start.hand_out(db, LATER) == 0

    end(db, own_first)
    assert competition_readiness.release(db, LATER) == [of_round(mine, 2)[0]["_id"]]
    assert season_start.hand_out(db, LATER) == 1


def test_an_account_game_of_a_later_round_waits_for_the_bots(db):
    (account,) = add_accounts(db, 1)
    season = running_season(db, add_bots(db, 3), [account], games_per_pairing=1)
    games = season_games(db, season["_id"])
    mine = [game for game in games if competition_readiness.color_of(game, account["_id"])]
    end(db, of_round(mine, 1)[0])

    assert competition_readiness.release(db, LATER) == []


def test_a_round_robin_edition_is_paced_like_a_league(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, games_per_pairing=1)
    enter(db, tournament, add_bots(db, 4))
    edition = start(db, tournament)
    games = edition_matches(db, edition["_id"])
    assert with_job(db, games) == [(None, 1, 1), (None, 1, 2)]

    for game in of_round(games, 1):
        end(db, game)
    edition_progress.advance_running(db, T0, random.Random(1))

    assert with_job(db, games) == [(None, 1, 1), (None, 1, 2), (None, 2, 1), (None, 2, 2)]


def test_only_leagues_and_round_robins_are_paced(db):
    season_id, edition_id = ObjectId(), ObjectId()
    league_game = {"season_id": season_id, "tier": 2, "round": 3}
    round_robin = {"edition_id": edition_id, "format": tournaments.ROUND_ROBIN, "round": 1}

    assert competition_pace.group(league_game) == {
        "context.season_id": season_id,
        "context.tier": 2,
    }
    assert competition_pace.group(round_robin) == {"context.edition_id": edition_id}
    for kind in (tournaments.SWISS, tournaments.KNOCKOUT):
        context = {"edition_id": edition_id, "format": kind, "round": 9}
        assert competition_pace.group(context) is None
        assert competition_pace.due(db, context, {})
