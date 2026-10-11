"""Accounts in leagues and tournaments: release, readiness, absence and reset (E182–E185)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_accounts, add_bots, add_league, register, register_accounts
from tournament_world import add_tournament, edition_matches, enter, start

from sbm_store import (
    competition_readiness,
    edition_progress,
    jobs,
    knockout_bracket,
    league_setup,
    matches,
    play,
    season_start,
    seasons,
    tournaments,
)
from sbm_store.names import JOBS, MATCHES, USERS
from sbm_store.registrations import TOURNAMENT

LATER = T0 + timedelta(minutes=1)
DEADLINE = LATER + timedelta(hours=2)


def league_with(db, accounts: list[dict], entrants: list[dict]) -> list[dict]:
    """A running season of the accounts and bots, one game per pairing; its games in order."""
    league = add_league(db, games_per_pairing=1, ready_hours=2)
    register(db, league, entrants)
    register_accounts(db, league, accounts)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, LATER, random.Random(1))
    season = seasons.latest(db, league["_id"])
    return list(
        db[MATCHES].find({"context.season_id": season["_id"]}).sort(competition_readiness.ORDER)
    )


def with_account(games: list[dict]) -> list[dict]:
    return [game for game in games if "human" in (game["white"]["kind"], game["black"]["kind"])]


def released(db) -> list[dict]:
    return list(db[MATCHES].find({"readiness": {"$ne": None}}).sort(competition_readiness.ORDER))


def get(db, match_id):
    return matches.get(db, match_id)


def ready(db, match: dict, account: dict, now=LATER, seat_hash: str = "hash") -> dict | None:
    color = competition_readiness.color_of(match, account["_id"])
    return competition_readiness.mark_ready(db, match["_id"], color, seat_hash, now)


def play_jobs(db, match_id) -> list[dict]:
    return list(db[JOBS].find({"type": jobs.PLAY, "payload.match_id": match_id}))


def test_a_season_lays_out_account_games_without_a_job(db):
    (account,) = add_accounts(db, 1)
    games = league_with(db, [account], add_bots(db, 2))

    season = db["seasons"].find_one({"status": seasons.RUNNING})
    (entry,) = [each for each in season["tiers"][0]["entries"] if each["user_id"] is not None]
    assert entry | {"lot": 0} == {
        "bot_id": None,
        "user_id": account["_id"],
        "name": "Player0",
        "version": None,
        "lot": 0,
    }
    mine = with_account(games)
    assert len(games) == 3
    assert len(mine) == 2
    for game in mine:
        side = game[competition_readiness.color_of(game, account["_id"])]
        assert side["kind"] == play.HUMAN
        assert side["seat_hash"] is None
        assert game["rated"]
        assert "readiness" not in game
        assert db[JOBS].count_documents({"payload.match_id": game["_id"]}) == 0
    (between_bots,) = [game for game in games if game not in mine]
    assert db[JOBS].count_documents({"type": jobs.MATCH, "payload.match_id": between_bots["_id"]})


def test_release_hands_out_one_game_per_account_in_order(db):
    (account,) = add_accounts(db, 1)
    first, second = with_account(league_with(db, [account], add_bots(db, 2)))

    assert competition_readiness.release(db, LATER) == [first["_id"]]
    assert competition_readiness.release(db, LATER) == []

    readiness = get(db, first["_id"])["readiness"]
    color = competition_readiness.color_of(first, account["_id"])
    other = "black" if color == "white" else "white"
    assert readiness["deadline"] == DEADLINE
    assert readiness["started_at"] is None
    assert readiness[color] == {"ready_at": None, "seen_at": None}
    assert readiness[other] is None
    assert competition_readiness.waiting_for_ready(get(db, first["_id"]))

    db[MATCHES].update_one({"_id": first["_id"]}, {"$set": {"status": matches.FINISHED}})
    assert competition_readiness.release(db, DEADLINE) == [second["_id"]]


def test_a_ready_and_present_account_starts_its_game_at_once(db):
    (account,) = add_accounts(db, 1)
    first, _ = with_account(league_with(db, [account], add_bots(db, 2)))
    competition_readiness.release(db, LATER)

    marked = ready(db, first, account)

    color = competition_readiness.color_of(first, account["_id"])
    assert marked["readiness"][color] == {"ready_at": LATER, "seen_at": LATER}
    assert marked[color]["seat_hash"] == "hash"
    assert competition_readiness.side_state(marked["readiness"][color], LATER) == {
        "ready": True,
        "present": True,
    }
    assert competition_readiness.start_ready(db, LATER) == [first["_id"]]
    assert competition_readiness.start_ready(db, LATER) == []
    (job,) = play_jobs(db, first["_id"])
    assert job["payload"]["competition"] is True
    assert ready(db, first, account) is None


def test_a_ready_but_gone_account_starts_at_the_deadline(db):
    (account,) = add_accounts(db, 1)
    first, _ = with_account(league_with(db, [account], add_bots(db, 2)))
    competition_readiness.release(db, LATER)
    ready(db, first, account)
    ready(db, first, account, now=LATER + timedelta(seconds=10))

    gone = LATER + timedelta(minutes=1)
    color = competition_readiness.color_of(first, account["_id"])
    side = get(db, first["_id"])["readiness"][color]
    assert side["ready_at"] == LATER
    assert competition_readiness.side_state(side, gone) == {"ready": True, "present": False}
    assert competition_readiness.start_ready(db, gone) == []
    assert competition_readiness.expire(db, DEADLINE) == []
    assert competition_readiness.start_ready(db, DEADLINE) == [first["_id"]]
    assert len(play_jobs(db, first["_id"])) == 1


def test_an_absent_account_loses_unplayed_and_the_next_game_follows(db):
    (account,) = add_accounts(db, 1)
    first, second = with_account(league_with(db, [account], add_bots(db, 2)))
    competition_readiness.release(db, LATER)

    assert competition_readiness.expire(db, DEADLINE - timedelta(seconds=1)) == []
    assert competition_readiness.start_ready(db, DEADLINE) == []
    assert competition_readiness.expire(db, DEADLINE) == [first["_id"]]

    ended = get(db, first["_id"])
    lost = "0-1" if competition_readiness.color_of(first, account["_id"]) == "white" else "1-0"
    assert ended["status"] == matches.FINISHED
    assert ended["result"] == lost
    assert ended["termination"] == matches.FORFEIT_ABSENT
    assert not ended["rated"]
    assert ended["moves"] == []
    assert competition_readiness.release(db, DEADLINE) == [second["_id"]]


def test_both_accounts_absent_lose_and_one_ready_account_wins(db):
    accounts = add_accounts(db, 2)
    (game,) = league_with(db, accounts, [])
    competition_readiness.release(db, LATER)
    assert competition_readiness.expire(db, DEADLINE) == [game["_id"]]
    assert get(db, game["_id"])["result"] == "0-0"

    db[MATCHES].update_one(
        {"_id": game["_id"]},
        {"$set": {"status": matches.QUEUED, "readiness": None, "result": None}},
    )
    competition_readiness.release(db, LATER)
    ready(db, game, accounts[0])
    assert competition_readiness.start_ready(db, DEADLINE) == []
    assert competition_readiness.expire(db, DEADLINE) == [game["_id"]]
    won = "1-0" if competition_readiness.color_of(game, accounts[0]["_id"]) == "white" else "0-1"
    assert get(db, game["_id"])["result"] == won


def test_two_accounts_start_once_both_are_ready_and_present(db):
    accounts = add_accounts(db, 2)
    (game,) = league_with(db, accounts, [])
    competition_readiness.release(db, LATER)

    ready(db, game, accounts[0])
    assert competition_readiness.start_ready(db, LATER) == []
    ready(db, game, accounts[1], seat_hash="other")
    assert competition_readiness.start_ready(db, LATER) == [game["_id"]]

    started = get(db, game["_id"])
    assert {started["white"]["seat_hash"], started["black"]["seat_hash"]} == {"hash", "other"}


def test_reset_releases_a_failed_game_anew(db):
    (account,) = add_accounts(db, 1)
    first, _ = with_account(league_with(db, [account], add_bots(db, 2)))
    competition_readiness.release(db, LATER)
    ready(db, first, account)
    competition_readiness.start_ready(db, LATER)
    assert matches.start(db, first["_id"], LATER)
    matches.append_move(db, first["_id"], {"uci": "e2e4"})

    again = LATER + timedelta(hours=1)
    assert competition_readiness.reset(db, first["_id"], again)

    match = get(db, first["_id"])
    color = competition_readiness.color_of(first, account["_id"])
    assert match["status"] == matches.QUEUED
    assert match["moves"] == []
    assert match["started_at"] is None
    assert match[color]["seat_hash"] is None
    assert match["readiness"]["released_at"] == again
    assert match["readiness"]["deadline"] == again + timedelta(hours=2)
    assert match["readiness"]["started_at"] is None
    assert match["readiness"][color] == {"ready_at": None, "seen_at": None}
    assert competition_readiness.release(db, again) == []

    db[MATCHES].update_one({"_id": first["_id"]}, {"$set": {"status": matches.FINISHED}})
    assert not competition_readiness.reset(db, first["_id"], again)


def test_reset_leaves_games_without_readiness_alone(db):
    (account,) = add_accounts(db, 1)
    games = league_with(db, [account], add_bots(db, 2))
    (between_bots,) = [game for game in games if game not in with_account(games)]

    assert not competition_readiness.reset(db, between_bots["_id"], LATER)
    assert competition_readiness.is_competition(between_bots)


def test_cancelling_a_started_game_cancels_its_play_job(db):
    (account,) = add_accounts(db, 1)
    first, _ = with_account(league_with(db, [account], add_bots(db, 2)))
    competition_readiness.release(db, LATER)
    ready(db, first, account)
    competition_readiness.start_ready(db, LATER)

    cancelled = jobs.cancel_match(db, first["_id"], LATER)

    assert cancelled["type"] == jobs.PLAY
    assert play_jobs(db, first["_id"])[0]["status"] == jobs.CANCELLED


def test_an_inactive_account_does_not_start_in_a_season(db):
    accounts = add_accounts(db, 2)
    db[USERS].update_one({"_id": accounts[1]["_id"]}, {"$set": {"active": False}})

    games = league_with(db, accounts, add_bots(db, 1))

    assert len(games) == 1
    assert competition_readiness.color_of(games[0], accounts[1]["_id"]) is None


def test_an_edition_seeds_accounts_by_rating_and_lays_out_their_games(db):
    tournament = add_tournament(db, tournaments.ROUND_ROBIN, games_per_pairing=1)
    (account,) = add_accounts(db, 1)
    key = f"ratings.{tournament['discipline_id']}"
    db[USERS].update_one(
        {"_id": account["_id"]}, {"$set": {key: {"value": 3000, "games": 9, "seq": 1}}}
    )
    enter(db, tournament, add_bots(db, 2))
    register_accounts(db, tournament, [account], target_type=TOURNAMENT)

    edition = start(db, tournament)

    first = edition["participants"][0]
    assert (first["user_id"], first["bot_id"], first["rating"], first["seed"]) == (
        account["_id"],
        None,
        3000,
        1,
    )
    games = edition_matches(db, edition["_id"])
    mine = with_account(games)
    assert len(games) == 3
    assert len(mine) == 2
    assert all(db[JOBS].count_documents({"payload.match_id": game["_id"]}) == 0 for game in mine)
    assert competition_readiness.release(db, LATER) == [
        min(mine, key=lambda game: game["context"]["round"])["_id"]
    ]


def test_absence_decides_a_knockout_duel_at_once(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=2, ready_hours=2)
    (account,) = add_accounts(db, 1)
    (bot,) = add_bots(db, 1)
    enter(db, tournament, [bot])
    register_accounts(db, tournament, [account], target_type=TOURNAMENT)
    edition = start(db, tournament)
    edition_progress.advance_running(db, LATER, random.Random(1))
    first, second = edition_matches(db, edition["_id"], matches.QUEUED)
    assert competition_readiness.release(db, LATER) == [first["_id"]]

    assert competition_readiness.expire(db, DEADLINE) == [first["_id"]]
    edition_progress.advance_running(db, DEADLINE, random.Random(1))
    edition_progress.advance_running(db, DEADLINE, random.Random(1))

    finished = db["editions"].find_one({"_id": edition["_id"]})
    (duel,) = finished["duels"]
    assert duel["decided_by"] == knockout_bracket.ABSENCE
    assert duel["winner"] == bot["_id"]
    assert finished["status"] == "finished"
    assert finished["winner"]["bot_id"] == bot["_id"]
    assert get(db, second["_id"])["status"] == matches.ABORTED


def test_both_absent_in_a_final_leave_no_winner(db):
    tournament = add_tournament(db, tournaments.KNOCKOUT, games_per_pairing=1, ready_hours=2)
    accounts = add_accounts(db, 2)
    register_accounts(db, tournament, accounts, target_type=TOURNAMENT)
    edition = start(db, tournament)
    edition_progress.advance_running(db, LATER, random.Random(1))
    competition_readiness.release(db, LATER)
    competition_readiness.expire(db, DEADLINE)

    edition_progress.advance_running(db, DEADLINE, random.Random(1))
    edition_progress.advance_running(db, DEADLINE, random.Random(1))

    finished = db["editions"].find_one({"_id": edition["_id"]})
    assert finished["duels"][0]["winner"] is None
    assert finished["status"] == "finished"
    assert finished["winner"] is None
