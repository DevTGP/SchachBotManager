from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import bots, matches, rankings, rating_settings, rating_values, ratings
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate
from sbm_store.names import BOTS, MATCHES
from sbm_store.rating_rule import DEFAULT, RatingRule

RATED = Discipline("Blitz", initial_time_ms=60_000, discipline_id=ObjectId())
RAPID = Discipline("Rapid", initial_time_ms=600_000, discipline_id=ObjectId())
FREE = Discipline("Free", initial_time_ms=60_000)


def add_bot(db, name: str, status: str = bots.VERIFIED) -> dict:
    bot = {"_id": ObjectId(), "name": name, "name_key": name.lower(), "version_no": 1}
    db[BOTS].insert_one(bot | {"status": status})
    return bot


def play(db, white, black, result, *, minute=0, discipline=RATED, finish=True):
    match_id = enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=T0)
    matches.start(db, match_id, T0)
    if finish:
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


def rating(db, bot, start: int = 2500, discipline: Discipline = RATED) -> dict:
    return rating_values.in_discipline(bots.get(db, bot["_id"]), discipline.discipline_id, start)


def value(db, bot) -> int:
    return rating(db, bot)["value"]


def test_a_bot_without_counted_matches_stands_at_the_start(db):
    migrate(db)

    assert rating(db, add_bot(db, "A")) == {"value": 2500, "games": 0}
    assert rating_values.overall(None, 2500) == {"value": 2500, "games": 0}


def test_rated_matches_are_counted_in_the_order_they_finished(db):
    migrate(db)
    a, b, c = add_bot(db, "A"), add_bot(db, "B"), add_bot(db, "C")
    second = play(db, a, c, "1-0", minute=2)
    first = play(db, a, b, "1-0", minute=1)

    assert ratings.count_pending(db) == 2

    assert (value(db, a), value(db, b), value(db, c)) == (2550 + 48, 2450, 2500 - 48)
    assert matches.get(db, first)["rating"] == {
        "seq": 1,
        "white": {"before": 2500, "after": 2550, "games": 1},
        "black": {"before": 2500, "after": 2450, "games": 1},
    }
    assert matches.get(db, second)["rating"]["seq"] == 2
    assert rating(db, a) == {"value": 2598, "games": 2}


def test_the_rule_comes_from_the_settings(db):
    migrate(db)
    rating_settings.save(db, RatingRule(start=1000, base=10))
    a, b = add_bot(db, "A"), add_bot(db, "B")
    play(db, a, b, "1-0")

    assert ratings.count_pending(db) == 1

    assert rating(db, a, 1000) == {"value": 1010, "games": 1}
    assert rating(db, b, 1000) == {"value": 990, "games": 1}


def test_unrated_aborted_and_unfinished_matches_change_nothing(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    free = play(db, a, b, "1-0", discipline=FREE)
    running = play(db, a, b, "1-0", finish=False)
    aborted = play(db, a, b, "1-0", finish=False)
    matches.abort(db, aborted, "infrastructure", T0)

    assert ratings.count_pending(db) == 0
    assert (value(db, a), value(db, b)) == (2500, 2500)
    assert all("rating" not in matches.get(db, m) for m in (free, running, aborted))


def test_counting_again_changes_nothing(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    play(db, a, b, "1/2-1/2")
    play(db, a, b, "0-1", minute=1)

    assert ratings.count_pending(db) == 2
    assert ratings.count_pending(db) == 0
    assert (value(db, a), value(db, b)) == (2450, 2550)


def test_a_crash_after_the_claim_is_repaired_before_the_next_match(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    play(db, a, b, "1-0")
    ratings.count_pending(db)
    # The second match is claimed, but the bots never got their new values.
    second = play(db, a, b, "1-0", minute=1)
    saved = {bot["_id"]: bot["ratings"] for bot in db[BOTS].find({"ratings": {"$exists": True}})}
    ratings.count_pending(db)
    for bot_id, entries in saved.items():
        db[BOTS].update_one({"_id": bot_id}, {"$set": {"ratings": entries}})
    play(db, b, a, "1/2-1/2", minute=2)

    assert ratings.count_pending(db) == 1

    assert matches.get(db, second)["rating"]["white"]["after"] == 2595
    assert rating(db, a) == {"value": 2595 - 9, "games": 3}
    assert rating(db, b) == {"value": 2405 + 9, "games": 3}


def test_a_number_taken_by_another_runner_is_not_used_twice(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    first_id = play(db, a, b, "1-0")
    other = play(db, b, a, "1-0", minute=1)
    db[MATCHES].update_one({"_id": other}, {"$set": {"rating": _claimed(1)}})
    ratings._settle_last(db)
    first = matches.get(db, first_id)

    assert not ratings._count(db, first, 1, DEFAULT)
    assert ratings.count_pending(db) == 1
    assert matches.get(db, first_id)["rating"]["seq"] == 2


def test_a_bot_against_itself_is_never_rated(db):
    migrate(db)
    a = add_bot(db, "A")
    match_id = play(db, a, a, "1-0")
    assert not matches.get(db, match_id)["rated"]

    db[MATCHES].update_one({"_id": match_id}, {"$set": {"rated": True}})
    assert ratings.count_pending(db) == 0
    assert not matches.get(db, match_id)["rated"]
    assert value(db, a) == 2500


def test_the_ranking_holds_public_bots_with_counted_matches(db):
    migrate(db)
    a, b, c = add_bot(db, "A"), add_bot(db, "B"), add_bot(db, "C")
    hidden = add_bot(db, "Hidden", status=bots.UPLOADED)
    add_bot(db, "Idle")
    play(db, a, b, "0-1")
    play(db, c, hidden, "1/2-1/2", minute=1)
    ratings.count_pending(db)

    ranking = rankings.bot_ranking(db, None, 2500)
    assert [(bot["name"], entry["value"]) for bot, entry in ranking] == [
        ("B", 2550),
        ("C", 2500),
        ("A", 2450),
    ]


def test_each_discipline_has_its_own_rating(db):
    migrate(db)
    a, b = add_bot(db, "A"), add_bot(db, "B")
    play(db, a, b, "1-0")
    play(db, a, b, "0-1", minute=1, discipline=RAPID)
    ratings.count_pending(db)

    assert rating(db, a) == {"value": 2550, "games": 1}
    assert rating(db, a, discipline=RAPID) == {"value": 2450, "games": 1}
    play(db, b, a, "1-0", minute=2, discipline=RAPID)
    ratings.count_pending(db)
    # The favourite in Rapid wins 45, where the underdog in Blitz would have won 55.
    assert rating(db, b, discipline=RAPID) == {"value": 2550 + 45, "games": 2}
    assert rating(db, b) == {"value": 2450, "games": 1}


def test_the_rankings_of_a_discipline_hold_only_its_games(db):
    migrate(db)
    a, b, c = add_bot(db, "A"), add_bot(db, "B"), add_bot(db, "C")
    play(db, a, b, "1-0")
    play(db, c, a, "1-0", minute=1, discipline=RAPID)
    ratings.count_pending(db)

    blitz = rankings.bot_ranking(db, RATED.discipline_id, 2500)
    rapid = rankings.bot_ranking(db, RAPID.discipline_id, 2500)
    overall = rankings.bot_ranking(db, None, 2500)

    assert [(bot["name"], entry["value"]) for bot, entry in blitz] == [("A", 2550), ("B", 2450)]
    assert [(bot["name"], entry["value"]) for bot, entry in rapid] == [("C", 2550), ("A", 2450)]
    assert [(bot["name"], entry) for bot, entry in overall] == [
        ("C", {"value": 2550, "games": 1}),
        ("A", {"value": 2500, "games": 2}),
        ("B", {"value": 2450, "games": 1}),
    ]
    assert rankings.bot_ranking(db, ObjectId(), 2500) == []


def _claimed(seq: int) -> dict:
    side = {"before": 2500, "after": 2500, "games": 1}
    return {"seq": seq, "white": side, "black": side}
