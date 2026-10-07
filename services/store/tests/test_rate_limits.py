from datetime import timedelta

from conftest import T0

from sbm_store import rate_limits
from sbm_store.names import RATE_LIMITS

WINDOW = timedelta(minutes=15)


def hit(db, key, minutes):
    return rate_limits.hit(db, key, now=T0 + timedelta(minutes=minutes), window=WINDOW)


def test_requests_count_per_key_and_window(db):
    assert [hit(db, "auth:1.2.3.4", minute).requests for minute in (0, 1, 14)] == [1, 2, 3]
    assert hit(db, "auth:5.6.7.8", 1).requests == 1
    assert hit(db, "auth:1.2.3.4", 15).requests == 1


def test_a_counter_expires_with_its_window(db):
    count = hit(db, "auth:1.2.3.4", 3)

    assert count.resets_at == T0 + WINDOW
    assert db[RATE_LIMITS].find_one()["expires_at"] == T0 + WINDOW
