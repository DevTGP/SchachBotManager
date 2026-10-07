from datetime import timedelta

from sbm_api.queue_estimate import schedule

from stored_games import BLITZ, NOW

TEN_MINUTES = timedelta(minutes=10)


def match(started_minutes_ago: int | None = None) -> dict:
    started = None if started_minutes_ago is None else NOW - timedelta(minutes=started_minutes_ago)
    return {"started_at": started, "discipline_snapshot": BLITZ.to_document()}


def ten_minutes(_discipline: dict) -> timedelta:
    return TEN_MINUTES


def test_two_slots_share_the_waiting_matches():
    running, waiting = schedule(
        [match(started_minutes_ago=4)],
        [(match(), NOW), (match(), NOW), (match(), NOW)],
        slots=2,
        now=NOW,
        duration=ten_minutes,
    )
    assert running == [(NOW - timedelta(minutes=4), NOW + timedelta(minutes=6))]
    starts = [start for start, _ in waiting]
    assert starts == [NOW, NOW + timedelta(minutes=6), NOW + TEN_MINUTES]


def test_more_running_matches_than_slots_all_count():
    # After the parallelism was lowered, the running matches still finish first.
    _, waiting = schedule(
        [match(started_minutes_ago=8), match(started_minutes_ago=2)],
        [(match(), NOW)],
        slots=1,
        now=NOW,
        duration=ten_minutes,
    )
    assert waiting == [(NOW + timedelta(minutes=2), NOW + timedelta(minutes=12))]
