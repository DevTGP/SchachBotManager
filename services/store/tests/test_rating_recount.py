from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import bots, matches, rating_recount, ratings
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate
from sbm_store.names import BOTS, MATCHES, SETTINGS

RATED = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())


def add_bot(db, name: str) -> dict:
    bot = {"_id": ObjectId(), "name": name, "name_key": name.lower(), "version_no": 1}
    db[BOTS].insert_one(bot | {"status": bots.VERIFIED})
    return bot


def play(db, white, black, result, *, minute) -> ObjectId:
    match_id = enqueue_match(db, white, black, RATED, start_fen=STANDARD_FEN, now=T0)
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


def token(db):
    return db[SETTINGS].find_one({"_id": rating_recount.DOCUMENT_ID})["recount_request"]


def test_nothing_happens_without_a_request(db):
    migrate(db)

    assert not rating_recount.is_requested(db)
    assert rating_recount.run_if_requested(db) is None


def test_a_recount_counts_the_remaining_matches_from_the_start(db):
    migrate(db)
    a, b, c = add_bot(db, "A"), add_bot(db, "B"), add_bot(db, "C")
    gone = play(db, a, b, "1-0", minute=1)
    kept = play(db, a, c, "1-0", minute=2)
    ratings.count_pending(db)
    db[MATCHES].delete_one({"_id": gone})
    db[BOTS].delete_one({"_id": b["_id"]})

    rating_recount.request(db, T0)
    assert rating_recount.is_requested(db)
    assert rating_recount.run_if_requested(db) == 1

    assert not rating_recount.is_requested(db)
    assert matches.get(db, kept)["rating"] == {
        "seq": 1,
        "white": {"before": 2500, "after": 2550, "games": 1},
        "black": {"before": 2500, "after": 2450, "games": 1},
    }
    assert ratings.current(bots.get(db, a["_id"])) == {"value": 2550, "games": 1}
    assert ratings.current(bots.get(db, c["_id"])) == {"value": 2450, "games": 1}


def test_a_bot_without_remaining_matches_is_back_at_the_start(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    gone = play(db, a, b, "1-0", minute=1)
    ratings.count_pending(db)
    db[MATCHES].delete_one({"_id": gone})

    rating_recount.request(db, T0)
    assert rating_recount.run_if_requested(db) == 0

    assert "rating" not in bots.get(db, a["_id"])
    assert ratings.current(bots.get(db, b["_id"])) == {"value": 2500, "games": 0}


def test_a_request_made_during_the_recount_stays(db, monkeypatch):
    migrate(db)
    rating_recount.request(db, T0)
    first = token(db)
    recount = rating_recount.recount

    def recount_while_asked_again(database):
        rating_recount.request(database, T0)
        return recount(database)

    monkeypatch.setattr(rating_recount, "recount", recount_while_asked_again)
    assert rating_recount.run_if_requested(db) == 0
    monkeypatch.undo()

    assert token(db) not in (None, first)
    assert rating_recount.run_if_requested(db) == 0
    assert not rating_recount.is_requested(db)
