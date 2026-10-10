from datetime import timedelta

from bson import ObjectId
from conftest import BLITZ, START_FEN, T0

from sbm_store import matches
from sbm_store.discipline import Discipline
from sbm_store.enqueue import enqueue_match

MOVE = {
    "ply": 1,
    "uci": "e2e4",
    "san": "e4",
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "spent_ms": 5,
    "clock_ms": 60_995,
    "info": None,
}


def enqueue(db, white, black, *, minutes=0):
    now = T0 + timedelta(minutes=minutes)
    return enqueue_match(db, white, black, BLITZ, start_fen=START_FEN, now=now)


def test_a_match_runs_through_its_life(db, reference_bots):
    match_id = enqueue(db, *reference_bots)

    assert matches.start(db, match_id, T0)
    assert not matches.start(db, match_id, T0)
    matches.append_move(db, match_id, MOVE)
    matches.finish(
        db,
        match_id,
        sides={"white": {"sdk": "python/0.1.0", "lang": "python"}},
        result="1-0",
        termination="checkmate",
        detail="checkmate",
        now=T0 + timedelta(minutes=2),
    )

    match = matches.get(db, match_id)
    assert match["status"] == matches.FINISHED
    assert match["moves"] == [MOVE]
    assert match["white"]["sdk"] == "python/0.1.0"
    assert match["black"]["sdk"] is None
    assert (match["result"], match["termination"]) == ("1-0", "checkmate")
    assert matches.recent_durations_ms(db, "Blitz", 5) == [120_000]


def test_requeue_discards_the_game_so_far(db, reference_bots):
    match_id = enqueue(db, *reference_bots)
    matches.start(db, match_id, T0)
    matches.append_move(db, match_id, MOVE)

    matches.requeue(db, match_id)

    match = matches.get(db, match_id)
    assert (match["status"], match["moves"], match["started_at"]) == (matches.QUEUED, [], None)


def test_abort_ends_without_result(db, reference_bots):
    match_id = enqueue(db, *reference_bots)

    matches.abort(db, match_id, "runner lost 3 times", T0)

    match = matches.get(db, match_id)
    assert (match["status"], match["result"], match["termination"]) == (
        matches.ABORTED,
        "*",
        "aborted",
    )


def test_pages_are_newest_first_without_moves(db, reference_bots):
    white, black = reference_bots
    ids = [enqueue(db, white, black, minutes=minute) for minute in range(3)]
    matches.start(db, ids[0], T0)
    matches.append_move(db, ids[0], MOVE)

    items, total = matches.page(db, {}, limit=2, offset=1)

    assert total == 3
    assert [item["_id"] for item in items] == [ids[1], ids[0]]
    assert "moves" not in items[1]
    assert items[1]["ply_count"] == 1


def test_filters_by_status_and_bot(db, reference_bots):
    white, black = reference_bots
    first = enqueue(db, white, black)
    second = enqueue(db, black, black, minutes=1)
    matches.start(db, second, T0)

    def ids(query):
        return [item["_id"] for item in matches.page(db, query, limit=10, offset=0)[0]]

    assert ids(matches.match_filter(status=matches.QUEUED)) == [first]
    assert ids(matches.match_filter(bot_id=white["_id"])) == [first]
    assert ids(matches.match_filter(bot_id=black["_id"])) == [second, first]
    assert ids(matches.match_filter(status=matches.RUNNING, bot_id=white["_id"])) == []


def test_summaries_by_id(db, reference_bots):
    match_id = enqueue(db, *reference_bots)

    assert matches.summaries(db, [match_id])[match_id]["ply_count"] == 0


def test_filters_by_opponent_discipline_and_requester(db, reference_bots):
    white, black = reference_bots
    rated = Discipline("Rated", initial_time_ms=60_000, discipline_id=ObjectId())
    account = ObjectId()
    pair = enqueue(db, white, black)
    reverse = enqueue_match(
        db, black, white, rated, start_fen=START_FEN, now=T0 + timedelta(minutes=1)
    )
    own = enqueue_match(
        db,
        black,
        black,
        BLITZ,
        start_fen=START_FEN,
        now=T0 + timedelta(minutes=2),
        created_by=account,
    )

    def ids(query):
        return [item["_id"] for item in matches.page(db, query, limit=10, offset=0)[0]]

    both = matches.match_filter(bot_id=white["_id"], opponent_id=black["_id"])
    assert ids(both) == [reverse, pair]
    assert ids(matches.match_filter(bot_id=black["_id"], opponent_id=black["_id"])) == [own]
    assert ids(matches.match_filter(discipline_id=rated.discipline_id)) == [reverse]
    assert ids(matches.match_filter(created_by=account)) == [own]


def test_optional_fields_stay_out_unless_set(db, reference_bots):
    match = matches.get(db, enqueue(db, *reference_bots))

    assert not {"series", "created_by", "counted"} & match.keys()


def test_a_series_reads_in_its_order(db, reference_bots):
    white, black = reference_bots
    series_id = ObjectId()
    second = enqueue_match(
        db,
        black,
        white,
        BLITZ,
        start_fen=START_FEN,
        now=T0,
        series=matches.series_place(series_id, 2, 2),
    )
    first = enqueue_match(
        db,
        white,
        black,
        BLITZ,
        start_fen=START_FEN,
        now=T0,
        series=matches.series_place(series_id, 1, 2),
        created_by=ObjectId(),
        counted=True,
    )
    enqueue(db, white, black)

    games = matches.of_series(db, series_id)

    assert [game["_id"] for game in games] == [first, second]
    assert games[0]["series"] == {"id": series_id, "index": 1, "games": 2}
    assert matches.get(db, first)["counted"] is True


def test_rated_false_keeps_a_rated_discipline_unrated(db, reference_bots):
    rated = Discipline("Rated", initial_time_ms=60_000, discipline_id=ObjectId())

    def match(**options):
        match_id = enqueue_match(db, *reference_bots, rated, start_fen=START_FEN, now=T0, **options)
        return matches.get(db, match_id)

    assert match()["rated"] is True
    assert match(rated=False)["rated"] is False
