import pytest
from bson import ObjectId
from conftest import T0

from sbm_store import bot_deletion, bot_files, bots, jobs, matches, rating_recount, ratings
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate
from sbm_store.names import BOTS, JOBS, MATCHES, VERIFICATION_REPORTS

RATED = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())
FILES = [("bot.py", "source", b"print(1)\n")]


def upload(db, name="Test", previous=None, status=bots.VERIFIED) -> dict:
    bot_id = ObjectId()
    entries = bot_files.store_files(db, bot_id, FILES)
    bot = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=name,
        version="1.0",
        language="python",
        entry="bot.py",
        files=entries,
        source_hash=bot_files.source_hash(entries),
        owner_id=ObjectId(),
        previous=previous,
        now=T0,
    )
    assert bots.insert(db, bot | {"status": status})
    return bots.get(db, bot_id)


def play(db, white, black, *, finish=True) -> ObjectId:
    match_id = enqueue_match(db, white, black, RATED, start_fen=STANDARD_FEN, now=T0)
    matches.start(db, match_id, T0)
    if finish:
        matches.finish(
            db, match_id, sides={}, result="1-0", termination="checkmate", detail="", now=T0
        )
    return match_id


def test_a_bot_goes_with_its_files_reports_jobs_and_matches(db):
    migrate(db)
    random = bots.by_name(db, "Random")
    bot = upload(db)
    jobs.insert(db, jobs.new_verification_job(bot["_id"], now=T0))
    db[VERIFICATION_REPORTS].insert_one({"bot_id": bot["_id"]})
    played = play(db, bot, random)
    waiting = enqueue_match(db, random, bot, RATED, start_fen=STANDARD_FEN, now=T0)
    other = play(db, random, bots.by_name(db, "Material"))

    deletion = bot_deletion.delete_bot(db, bot["_id"], T0)

    assert (deletion.bot["_id"], deletion.matches, deletion.recount) == (bot["_id"], 2, False)
    assert bots.get(db, bot["_id"]) is None
    assert db[MATCHES].count_documents({"_id": {"$in": [played, waiting]}}) == 0
    assert matches.get(db, other) is not None
    assert db[JOBS].count_documents({"payload.bot_id": bot["_id"]}) == 0
    assert db[JOBS].count_documents({"payload.match_id": {"$in": [played, waiting]}}) == 0
    assert db[JOBS].count_documents({"payload.match_id": other}) == 1
    assert db[VERIFICATION_REPORTS].count_documents({}) == 0
    assert db["bot_files.files"].count_documents({}) == 0
    assert not rating_recount.is_requested(db)


def test_deleting_a_counted_match_asks_for_a_recount(db):
    migrate(db)
    bot = upload(db)
    play(db, bot, bots.by_name(db, "Random"))
    ratings.count_pending(db)

    deletion = bot_deletion.delete_bot(db, bot["_id"], T0)

    assert deletion.recount
    assert rating_recount.is_requested(db)


def test_only_this_version_goes_and_the_name_is_free_once_none_is_left(db):
    migrate(db)
    first = upload(db)
    second = upload(db, previous=first)
    third = upload(db, previous=second)

    bot_deletion.delete_bot(db, second["_id"], T0)

    assert bots.get(db, first["_id"]) is not None
    assert bots.get(db, third["_id"])["parent_bot_id"] == first["_id"]
    assert bots.latest(db, "test")["_id"] == third["_id"]

    bot_deletion.delete_bot(db, first["_id"], T0)
    bot_deletion.delete_bot(db, third["_id"], T0)

    assert bots.latest(db, "Test") is None
    assert db[BOTS].count_documents({"name_key": "test"}) == 0


def test_a_missing_bot_is_none(db):
    migrate(db)

    assert bot_deletion.delete_bot(db, ObjectId(), T0) is None


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("builtin", bot_deletion.BUILTIN),
        ("playing", bot_deletion.PLAYING),
        ("testing", bot_deletion.VERIFYING),
    ],
)
def test_reference_bots_busy_bots_and_bots_in_verification_stay(db, kind, reason):
    migrate(db)
    random = bots.by_name(db, "Random")
    if kind == "builtin":
        bot = random
    elif kind == "playing":
        bot = upload(db)
        play(db, bot, random, finish=False)
    else:
        bot = upload(db, status=bots.TESTING)

    with pytest.raises(bot_deletion.NotDeletable) as raised:
        bot_deletion.delete_bot(db, bot["_id"], T0)

    assert raised.value.reason == reason
    assert bots.get(db, bot["_id"]) is not None
