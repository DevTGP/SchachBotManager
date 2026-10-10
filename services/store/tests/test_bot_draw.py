from bson import ObjectId

from sbm_store import bot_draw, bots
from sbm_store.names import BOTS


def add_bot(db, status: str = bots.VERIFIED) -> ObjectId:
    return db[BOTS].insert_one({"status": status}).inserted_id


def test_only_verified_bots_outside_exclude_are_drawn(db):
    first, second = add_bot(db), add_bot(db)
    add_bot(db, bots.REJECTED)
    add_bot(db, bots.UPLOADED)

    assert bot_draw.candidates(db, []) == 2
    assert bot_draw.candidates(db, [first]) == 1
    assert all(bot_draw.draw(db, [first])["_id"] == second for _ in range(10))
    assert bot_draw.draw(db, [first, second]) is None


def test_every_candidate_can_be_drawn(db):
    ids = {add_bot(db) for _ in range(3)}

    drawn = {bot_draw.draw(db, [])["_id"] for _ in range(60)}

    assert drawn == ids
