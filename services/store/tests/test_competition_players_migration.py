from bson import ObjectId
from pymongo import ASCENDING

from sbm_store import registrations
from sbm_store.migrate import migrate
from sbm_store.migrations import MIGRATIONS
from sbm_store.names import LEAGUES, MATCHES, REGISTRATIONS, TOURNAMENTS

MIGRATION = dict(MIGRATIONS)["0155_competition_players"]
INDEX = "target_type_1_target_id_1_bot_id_1_user_id_1"


def test_registrations_get_an_index_with_the_account(db):
    migrate(db)
    db[REGISTRATIONS].drop_index(INDEX)
    db[REGISTRATIONS].create_index(
        [("target_type", ASCENDING), ("target_id", ASCENDING), ("bot_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"status": "active"},
    )
    old = ObjectId()
    db[REGISTRATIONS].insert_one({"_id": old, "target_type": "league", "bot_id": ObjectId()})

    MIGRATION(db)
    MIGRATION(db)

    indexes = db[REGISTRATIONS].index_information()
    assert "target_type_1_target_id_1_bot_id_1" not in indexes
    assert indexes[INDEX]["unique"]
    assert db[REGISTRATIONS].find_one({"_id": old})["user_id"] is None
    assert "status_1_readiness.started_at_1" in db[MATCHES].index_information()


def test_two_accounts_register_once_each(db):
    migrate(db)
    league_id, first, second = ObjectId(), ObjectId(), ObjectId()

    def of(user_id):
        return registrations.new_registration(
            league_id, user_id=user_id, created_by=user_id, now=None
        )

    assert registrations.insert(db, of(first))
    assert registrations.insert(db, of(second))
    assert not registrations.insert(db, of(first))
    assert registrations.get_active(db, league_id, second)["user_id"] == second
    assert [entry["user_id"] for entry in registrations.active_of_bot(db, first)] == [first]


def test_leagues_and_tournaments_get_ready_hours(db):
    migrate(db)
    league, tournament, own = ObjectId(), ObjectId(), ObjectId()
    db[LEAGUES].insert_many(
        [{"_id": league, "name_key": "a"}, {"_id": own, "name_key": "b", "ready_hours": 6}]
    )
    db[TOURNAMENTS].insert_one({"_id": tournament, "name_key": "c"})

    MIGRATION(db)

    assert db[LEAGUES].find_one({"_id": league})["ready_hours"] == 48
    assert db[LEAGUES].find_one({"_id": own})["ready_hours"] == 6
    assert db[TOURNAMENTS].find_one({"_id": tournament})["ready_hours"] == 48
