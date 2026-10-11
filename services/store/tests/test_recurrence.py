"""The calendar of leagues and tournaments (E171)."""

from datetime import timedelta

from conftest import T0

from sbm_store import recurrence

DAILY = recurrence.new_recurrence(T0, 24)


def test_without_a_calendar_there_is_no_date():
    assert recurrence.next_slot(None, T0) is None


def test_before_the_first_start_comes_the_first_start():
    assert recurrence.next_slot(DAILY, T0 - timedelta(days=3)) == T0


def test_the_next_date_lies_after_the_given_time():
    assert recurrence.next_slot(DAILY, T0) == T0 + timedelta(days=1)
    assert recurrence.next_slot(DAILY, T0 + timedelta(hours=1)) == T0 + timedelta(days=1)
    assert recurrence.next_slot(DAILY, T0 + timedelta(days=2, hours=5)) == T0 + timedelta(days=3)


def test_inclusive_takes_a_date_at_the_given_time():
    assert recurrence.next_slot(DAILY, T0, inclusive=True) == T0
    later = T0 + timedelta(days=4)
    assert recurrence.next_slot(DAILY, later, inclusive=True) == later
    assert recurrence.next_slot(DAILY, later + timedelta(seconds=1), inclusive=True) == (
        T0 + timedelta(days=5)
    )
