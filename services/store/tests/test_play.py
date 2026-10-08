from datetime import timedelta

import pytest
from bson import ObjectId
from conftest import BLITZ, START_FEN, T0

from sbm_store import jobs, matches, play, play_settings, tokens
from sbm_store.discipline import Discipline
from sbm_store.names import JOBS

LEASE = timedelta(seconds=60)


def remote_side(seat_hash: str) -> dict:
    return play.seat_side(play.REMOTE, "alice", user_id=ObjectId(), seat_hash=seat_hash)


def test_a_seat_token_is_stored_only_as_its_hash():
    token, hashed = play.new_seat()
    assert len(token) == 43
    assert hashed == tokens.token_hash(token)
    assert token not in hashed


def test_create_stores_a_remote_match_unrated_with_a_play_job(db, reference_bots):
    _token, hashed = play.new_seat()
    match_id = play.create(
        db,
        play.REMOTE,
        remote_side(hashed),
        matches.side(reference_bots[0]),
        BLITZ,
        start_fen=START_FEN,
        now=T0,
    )

    match = matches.get(db, match_id)
    assert (match["type"], match["status"], match["rated"]) == ("remote", "queued", False)
    assert match["white"]["seat_hash"] == hashed
    assert match["white"]["bot_id"] is None
    assert play.is_seat(match["white"]) and not play.is_seat(match["black"])
    job = db[JOBS].find_one({"payload.match_id": match_id})
    assert (job["type"], job["status"]) == (play.PLAY_JOB, jobs.QUEUED)
    assert play.active_count(db) == 1


def test_the_queue_runner_never_claims_a_play_job(db, reference_bots):
    _token, hashed = play.new_seat()
    play.create(
        db,
        play.HUMAN,
        matches.side(reference_bots[1]),
        play.seat_side(play.HUMAN, "Guest", user_id=None, seat_hash=hashed),
        BLITZ,
        start_fen=START_FEN,
        now=T0,
    )
    assert jobs.claim(db, jobs.MATCH, "runner-1", now=T0, lease=LEASE) is None
    assert jobs.claim(db, play.PLAY_JOB, "play-1", now=T0, lease=LEASE) is not None


def test_an_interactive_match_needs_a_seat(reference_bots):
    with pytest.raises(ValueError):
        play.new_play_match(
            play.HUMAN,
            matches.side(reference_bots[0]),
            matches.side(reference_bots[1]),
            BLITZ,
            start_fen=START_FEN,
            now=T0,
        )


def test_unknown_kinds_are_rejected():
    with pytest.raises(ValueError):
        play.seat_side("bot", "x", user_id=None, seat_hash="0" * 64)


def test_interactive_games_are_not_rated_until_accounts_have_ratings(reference_bots):
    bot = matches.side(reference_bots[0])
    stored = Discipline("Blitz", 60_000, discipline_id=ObjectId())
    seat = play.seat_side(play.HUMAN, "x", user_id=ObjectId(), seat_hash="0" * 64)
    match = play.new_play_match(play.HUMAN, seat, bot, stored, start_fen=START_FEN, now=T0)
    assert match["rated"] is False


def test_active_games_are_counted_per_origin(db, reference_bots):
    user_id = ObjectId()
    requested = play.origin(ip_key="k1", user_id=user_id, token_id=None)
    _token, hashed = play.new_seat()
    side = play.seat_side(play.HUMAN, "alice", user_id=user_id, seat_hash=hashed)
    match_id = play.create(
        db,
        play.HUMAN,
        side,
        matches.side(reference_bots[0]),
        BLITZ,
        start_fen=START_FEN,
        now=T0,
        requested_by=requested,
    )
    assert play.active_by(db, "ip_key", "k1") == 1
    assert play.active_by(db, "user_id", user_id) == 1
    assert play.active_by(db, "ip_key", "k2") == 0
    matches.abort(db, match_id, "test", T0)
    assert play.active_by(db, "ip_key", "k1") == 0


def test_play_settings_have_defaults_and_can_be_saved(db):
    assert play_settings.get(db) == play_settings.PlaySettings(2, 1, 50)
    play_settings.save(db, play_settings.PlaySettings(max_games=3, games_per_day=10))
    assert play_settings.get(db) == play_settings.PlaySettings(3, 1, 10)
