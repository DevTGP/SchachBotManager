from datetime import timedelta

import pytest
from bson import ObjectId
from conftest import BLITZ, START_FEN, T0

from sbm_store import jobs, matches, play, tokens
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


def test_only_people_with_an_account_are_rated(reference_bots):
    bot = matches.side(reference_bots[0])
    stored = Discipline("Blitz", 60_000, discipline_id=ObjectId())

    def match(kind, user_id, discipline=stored, start_fen=START_FEN):
        seat = play.seat_side(kind, "x", user_id=user_id, seat_hash="0" * 64)
        return play.new_play_match(kind, seat, bot, discipline, start_fen=start_fen, now=T0)

    assert match(play.HUMAN, ObjectId())["rated"]
    assert not match(play.HUMAN, None)["rated"]
    assert not match(play.REMOTE, ObjectId())["rated"]
    assert not match(play.HUMAN, ObjectId(), discipline=BLITZ)["rated"]
    assert not match(play.HUMAN, ObjectId(), start_fen="8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")["rated"]
