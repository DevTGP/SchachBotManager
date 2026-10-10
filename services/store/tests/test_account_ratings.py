from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import bots, matches, play, rating_recount, ratings, users
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.migrate import migrate
from sbm_store.names import BOTS

RATED = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())


def add_bot(db, name: str) -> dict:
    bot = {"_id": ObjectId(), "name": name, "name_key": name.lower(), "version_no": 1}
    db[BOTS].insert_one(bot | {"status": bots.VERIFIED})
    return bot


def add_user(db, name: str) -> dict:
    user = users.new_user(name, "hash", users.PLAYER, invited_by=None, now=T0)
    users.insert(db, user)
    return user


def person_plays(db, user_id, bot, result, *, minute) -> ObjectId:
    """The person has White; user_id None is a guest."""
    _token, hashed = play.new_seat()
    seat = play.seat_side(play.HUMAN, "x", user_id=user_id, seat_hash=hashed)
    match_id = play.create(
        db, play.HUMAN, seat, matches.side(bot), RATED, start_fen=STANDARD_FEN, now=T0
    )
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


def value(db, collection_get, holder_id) -> dict:
    return ratings.current(collection_get(db, holder_id), 2500)


def test_a_game_of_an_account_moves_the_account_and_the_bot(db):
    migrate(db)
    alice, bot = add_user(db, "alice"), add_bot(db, "A")
    first = person_plays(db, alice["_id"], bot, "1-0", minute=1)
    person_plays(db, alice["_id"], bot, "1-0", minute=2)

    assert ratings.count_pending(db) == 2

    # The second game starts from the first: 2550 against 2450 is five steps apart.
    assert value(db, users.get, alice["_id"]) == {"value": 2550 + 45, "games": 2}
    assert value(db, bots.get, bot["_id"]) == {"value": 2450 - 45, "games": 2}
    assert matches.get(db, first)["rating"]["white"] == {"before": 2500, "after": 2550, "games": 1}


def test_a_guest_game_moves_nobody(db):
    migrate(db)
    bot = add_bot(db, "A")
    match_id = person_plays(db, None, bot, "1-0", minute=1)

    assert ratings.count_pending(db) == 0
    assert matches.get(db, match_id)["rated"] is False
    assert value(db, bots.get, bot["_id"]) == {"value": 2500, "games": 0}


def test_a_recount_starts_accounts_over_as_well(db):
    migrate(db)
    alice, a, b = add_user(db, "alice"), add_bot(db, "A"), add_bot(db, "B")
    person_plays(db, alice["_id"], a, "1-0", minute=1)
    ratings.count_pending(db)
    db[BOTS].delete_one({"_id": a["_id"]})
    db["matches"].delete_many({"black.bot_id": a["_id"]})
    person_plays(db, alice["_id"], b, "0-1", minute=2)
    rating_recount.request(db, T0)

    assert rating_recount.run_if_requested(db) == 1

    assert value(db, users.get, alice["_id"]) == {"value": 2450, "games": 1}
    assert value(db, bots.get, b["_id"]) == {"value": 2550, "games": 1}


def test_the_player_ranking_holds_active_accounts_with_counted_games(db):
    migrate(db)
    alice, bob, carol = add_user(db, "alice"), add_user(db, "Bob"), add_user(db, "carol")
    add_user(db, "idle")
    bot = add_bot(db, "A")
    person_plays(db, alice["_id"], bot, "0-1", minute=1)
    person_plays(db, bob["_id"], bot, "1-0", minute=2)
    person_plays(db, carol["_id"], bot, "1-0", minute=3)
    ratings.count_pending(db)
    users.update(db, carol["_id"], {"active": False})

    assert [user["username"] for user in ratings.player_ranking(db)] == ["Bob", "alice"]
