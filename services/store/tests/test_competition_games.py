from datetime import UTC, datetime, timedelta

from bson import ObjectId

from sbm_store import competition_games, matches
from sbm_store.discipline import Discipline

T0 = datetime(2026, 10, 1, tzinfo=UTC)
ACCOUNT = ObjectId()


def _discipline() -> Discipline:
    return Discipline(
        name="Blitz",
        initial_time_ms=60_000,
        increment_ms=0,
        startup_ms=10_000,
        tolerance_ms=1_000,
        max_moves=200,
    )


def _game(db, *, board, released=None, status=matches.QUEUED, account=ACCOUNT, kind="league"):
    person = {"_id": ObjectId(), "user_id": account, "name": "anna"}
    bot = {"_id": ObjectId(), "name": "Bot", "version": "1"}
    context = {"tier": 1, "round": 1, "board": board, "season_id": ObjectId()}
    match = matches.new_league_match(
        person, bot, _discipline(), context=context, priority=0, now=T0
    )
    match["type"] = kind
    match["status"] = status
    if released is not None:
        match["readiness"] = {"deadline": T0 + timedelta(hours=released)}
    matches.insert(db, match)
    return match["_id"]


def test_released_games_come_first_by_deadline_then_waiting_ones_in_order(db):
    waiting_late = _game(db, board=2)
    waiting_early = _game(db, board=1)
    released_late = _game(db, board=3, released=10)
    released_early = _game(db, board=4, released=5, status=matches.RUNNING)
    found = competition_games.of_account(db, ACCOUNT)
    assert [game["_id"] for game in found] == [
        released_early,
        released_late,
        waiting_early,
        waiting_late,
    ]


def test_finished_single_and_other_accounts_games_are_left_out(db):
    _game(db, board=1, status=matches.FINISHED)
    _game(db, board=2, account=ObjectId())
    _game(db, board=3, kind=matches.SINGLE)
    assert competition_games.of_account(db, ACCOUNT) == []
