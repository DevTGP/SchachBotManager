from bson import ObjectId

from sbm_store import rating_recount
from sbm_store.migrate import migrate
from sbm_store.migrations import MIGRATIONS
from sbm_store.names import BOTS, MATCHES, USERS

MIGRATION = dict(MIGRATIONS)["0153_discipline_ratings"]


def test_a_new_database_needs_no_recount(db):
    migrate(db)

    assert not rating_recount.is_requested(db)
    assert "rating.value_-1" not in db[BOTS].index_information()


def test_old_ratings_go_and_counted_matches_are_counted_again(db):
    migrate(db)
    bot_id, user_id = ObjectId(), ObjectId()
    db[BOTS].insert_one({"_id": bot_id, "rating": {"value": 2600, "games": 2, "seq": 2}})
    db[USERS].insert_one({"_id": user_id, "rating": {"value": 2400, "games": 2, "seq": 2}})
    db[MATCHES].insert_one({"_id": ObjectId(), "rating": {"seq": 2}})

    MIGRATION(db)
    MIGRATION(db)

    assert "rating" not in db[BOTS].find_one({"_id": bot_id})
    assert "rating" not in db[USERS].find_one({"_id": user_id})
    assert rating_recount.is_requested(db)
