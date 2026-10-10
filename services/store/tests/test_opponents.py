"""The head-to-head record of a bot (E161)."""

from datetime import timedelta

from bson import ObjectId
from conftest import BLITZ, START_FEN, T0

from sbm_store import matches, opponents
from sbm_store.enqueue import enqueue_match
from sbm_store.names import MATCHES


def play(db, white, black, result, *, minute=0, finish=True):
    now = T0 + timedelta(minutes=minute)
    match_id = enqueue_match(db, white, black, BLITZ, start_fen=START_FEN, now=now)
    matches.start(db, match_id, now)
    if finish:
        matches.finish(
            db, match_id, sides={}, result=result, termination="checkmate", detail="", now=now
        )
    return match_id


def bot(name: str, version: str | None = None) -> dict:
    return {"_id": ObjectId(), "name": name, "version": version}


def test_counts_from_the_bots_view_with_the_latest_name(db):
    me, often, once = bot("Me"), bot("Often", "1.0"), bot("Once")
    play(db, me, often, "1-0")
    play(db, often, me, "1-0", minute=1)
    play(db, often, me, "0-1", minute=2)
    newest = play(db, me, often, "1/2-1/2", minute=3)
    db[MATCHES].update_one({"_id": newest}, {"$set": {"black.version": "1.1"}})
    play(db, once, me, "1/2-1/2", minute=4)

    assert opponents.records(db, me["_id"]) == [
        {
            "_id": often["_id"],
            "name": "Often",
            "version": "1.1",
            "games": 4,
            "wins": 2,
            "draws": 1,
            "losses": 1,
        },
        {
            "_id": once["_id"],
            "name": "Once",
            "version": None,
            "games": 1,
            "wins": 0,
            "draws": 1,
            "losses": 0,
        },
    ]


def test_only_finished_games_against_other_bots(db):
    me, other = bot("Me"), bot("Other")
    play(db, me, me, "1-0")
    play(db, me, other, "1-0", finish=False)
    aborted = play(db, me, other, "1-0", finish=False)
    matches.abort(db, aborted, "cancelled", T0)
    human = play(db, me, other, "1-0")
    db[MATCHES].update_one({"_id": human}, {"$set": {"type": "human"}})

    assert opponents.records(db, me["_id"]) == []
