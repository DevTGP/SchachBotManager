"""The rating history of a bot per discipline (E140)."""

from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import bots, matches, rating_history, ratings
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate
from sbm_store.names import BOTS

BLITZ = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())
RAPID = Discipline("Rapid", initial_time_ms=600_000, discipline_id=ObjectId())
FREE = Discipline("Free", initial_time_ms=60_000)


def bot(db, name: str) -> dict:
    added = {"_id": ObjectId(), "name": name, "name_key": name.lower(), "version_no": 1}
    db[BOTS].insert_one(added | {"status": bots.VERIFIED})
    return added


def play(db, white, black, result, discipline, minute):
    match_id = enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=T0)
    matches.start(db, match_id, T0)
    matches.finish(
        db,
        match_id,
        sides={},
        result=result,
        termination="checkmate",
        detail="",
        now=T0 + timedelta(minutes=minute),
    )
    return match_id


def test_points_per_discipline_in_the_order_they_were_counted(db):
    migrate(db)
    me, other = bot(db, "Me"), bot(db, "Other")
    first = play(db, me, other, "1-0", BLITZ, 1)
    second = play(db, other, me, "1-0", BLITZ, 2)
    rapid = play(db, other, me, "0-1", RAPID, 3)
    play(db, me, other, "1-0", FREE, 4)
    ratings.count_pending(db)

    history = rating_history.of_bot(db, me["_id"])

    assert list(history) == [BLITZ.discipline_id, RAPID.discipline_id]
    blitz = history[BLITZ.discipline_id]
    assert [point.match_id for point in blitz] == [first, second]
    assert (blitz[0].before, blitz[0].after, blitz[1].before) == (2500, 2550, 2550)
    assert blitz[1].after < blitz[1].before
    assert blitz[0].finished_at.replace(tzinfo=None) == (T0 + timedelta(minutes=1)).replace(
        tzinfo=None
    )
    (point,) = history[RAPID.discipline_id]
    assert (point.match_id, point.before, point.after) == (rapid, 2500, 2550)


def test_no_history_without_counted_games(db):
    migrate(db)
    me, other = bot(db, "Me"), bot(db, "Other")
    play(db, me, other, "1-0", FREE, 1)
    ratings.count_pending(db)

    assert rating_history.of_bot(db, me["_id"]) == {}
