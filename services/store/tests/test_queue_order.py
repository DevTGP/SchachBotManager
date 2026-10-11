"""The order in which the runner takes matches across competitions (E134)."""

from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import jobs, queue_order
from sbm_store.migrate import migrate
from sbm_store.names import JOBS

LEASE = timedelta(seconds=60)
LEAGUE = jobs.league_competition(ObjectId())


def job(minute, competition=jobs.SINGLE, priority=50):
    return jobs.new_match_job(
        ObjectId(), priority=priority, now=T0 + timedelta(minutes=minute), competition=competition
    )


def test_competitions_take_turns_at_one_priority():
    single = [job(0), job(1)]
    league = [job(2, LEAGUE), job(3, LEAGUE)]

    ordered = queue_order.order(single + league, {})

    assert ordered == [single[0], league[0], single[1], league[1]]


def test_a_higher_priority_goes_first():
    urgent = job(5, priority=100)
    rest = [job(0), job(1, LEAGUE)]

    assert queue_order.order([*rest, urgent], {})[0] == urgent


def test_the_competition_served_longest_ago_goes_first():
    single, league = job(0), job(1, LEAGUE)
    claims = {jobs.SINGLE: T0 + timedelta(hours=1), LEAGUE: T0}

    assert queue_order.order([single, league], claims) == [league, single]
    assert queue_order.pick([single, league], claims) == league


def test_a_competition_never_served_goes_first():
    single, league = job(0), job(1, LEAGUE)

    assert queue_order.pick([single, league], {jobs.SINGLE: T0}) == league


def test_jobs_without_competition_count_as_single_games():
    old = job(0)
    del old["competition"]

    assert queue_order.competition(old) == jobs.SINGLE


def test_the_runner_alternates_between_competitions(db):
    migrate(db)
    waiting = [job(0), job(1), job(2, LEAGUE), job(3, LEAGUE)]
    db[JOBS].insert_many(waiting)
    now = T0 + timedelta(hours=1)

    taken = []
    for second in range(5):
        claimed = queue_order.claim_match(
            db, "w1", now=now + timedelta(seconds=second), lease=LEASE
        )
        taken.append(None if claimed is None else claimed["_id"])

    assert taken == [
        waiting[0]["_id"],
        waiting[2]["_id"],
        waiting[1]["_id"],
        waiting[3]["_id"],
        None,
    ]
    assert db[JOBS].find_one({"_id": waiting[0]["_id"]})["claimed_at"] == now


def test_the_waiting_list_shows_the_order_of_the_runner(db):
    migrate(db)
    single = [job(minute) for minute in range(3)]
    league = [job(10 + minute, LEAGUE) for minute in range(2)]
    db[JOBS].insert_many(single + league)

    shown, total = queue_order.waiting(db, 3)

    assert [entry["_id"] for entry in shown] == [
        single[0]["_id"],
        league[0]["_id"],
        single[1]["_id"],
    ]
    assert total == 5
