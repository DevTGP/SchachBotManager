"""Wins, draws and losses of a bot per discipline (E141)."""

from bson import ObjectId
from conftest import T0

from sbm_store import bot_record, matches
from sbm_store.bot_record import Counts
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.names import MATCHES

BLITZ = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())
FREE = Discipline("Free", initial_time_ms=60_000)


def bot(name: str) -> dict:
    return {"_id": ObjectId(), "name": name, "version": None}


def play(db, white, black, result, discipline=BLITZ, *, finish=True):
    match_id = enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=T0)
    matches.start(db, match_id, T0)
    if finish:
        matches.finish(
            db, match_id, sides={}, result=result, termination="checkmate", detail="", now=T0
        )
    return match_id


def test_counts_per_discipline_from_the_bots_view(db):
    me, other = bot("Me"), bot("Other")
    play(db, me, other, "1-0")
    play(db, other, me, "1-0")
    play(db, other, me, "0-1")
    play(db, me, other, "1/2-1/2")
    play(db, other, me, "1-0", FREE)

    assert bot_record.by_discipline(db, me["_id"]) == {
        BLITZ.discipline_id: Counts(wins=2, draws=1, losses=1),
        None: Counts(losses=1),
    }


def test_forfeits_and_people_count_but_not_itself_or_unfinished_games(db):
    me, other = bot("Me"), bot("Other")
    forfeit = play(db, other, me, "0-1", finish=False)
    db[MATCHES].update_one(
        {"_id": forfeit},
        {"$set": {"status": matches.FINISHED, "result": "0-1", "termination": matches.FORFEIT}},
    )
    human = play(db, me, other, "1-0")
    db[MATCHES].update_one({"_id": human}, {"$set": {"type": "human", "black": {"kind": "human"}}})
    play(db, me, me, "1-0")
    play(db, me, other, "1-0", finish=False)

    assert bot_record.by_discipline(db, me["_id"]) == {BLITZ.discipline_id: Counts(wins=2)}


def test_counts_add_up():
    total = Counts(wins=1, draws=2) + Counts(losses=3)
    assert (total, total.games) == (Counts(1, 2, 3), 6)
