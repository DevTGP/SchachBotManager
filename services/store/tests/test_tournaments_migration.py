from bson import ObjectId

from sbm_store.migrate import migrate
from sbm_store.migrations import MIGRATIONS
from sbm_store.names import EDITIONS, LEAGUES, MATCHES, SEASONS, TOURNAMENTS

MIGRATION = dict(MIGRATIONS)["0154_tournaments"]


def test_indexes_exist(db):
    migrate(db)

    assert "name_key_1" in db[TOURNAMENTS].index_information()
    assert "tournament_id_1_number_1" in db[EDITIONS].index_information()
    assert "context.edition_id_1_status_1" in db[MATCHES].index_information()


def test_a_pause_becomes_a_calendar(db):
    migrate(db)
    paused, short, plain = ObjectId(), ObjectId(), ObjectId()
    db[LEAGUES].insert_many(
        [
            {"_id": paused, "name_key": "a", "pause_minutes": 150},
            {"_id": short, "name_key": "b", "pause_minutes": 0},
            {"_id": plain, "name_key": "c"},
        ]
    )
    season_id = ObjectId()
    db[SEASONS].insert_one({"_id": season_id, "settings": {"pause_minutes": 150, "rounds": 2}})

    MIGRATION(db)
    MIGRATION(db)

    league = db[LEAGUES].find_one({"_id": paused})
    assert "pause_minutes" not in league
    assert league["recurrence"]["interval_hours"] == 3
    assert db[LEAGUES].find_one({"_id": short})["recurrence"]["interval_hours"] == 1
    assert db[LEAGUES].find_one({"_id": plain})["recurrence"] is None
    assert db[SEASONS].find_one({"_id": season_id})["settings"] == {"rounds": 2}
