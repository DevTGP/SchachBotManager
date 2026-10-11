import pytest
from sbm_store import disciplines, matches
from sbm_store.discipline import Discipline

from sbm_runner.enqueue_cli import EnqueueError, build_parser, enqueue_games
from sbm_runner.worker import utc_now


def enqueue(db, *argv: str):
    return enqueue_games(db, build_parser().parse_args(list(argv)), utc_now())


def test_queues_games_with_alternating_colors(db, reference_bots):
    ids = enqueue(db, "Random", "Material", "--games", "3", "--alternate", "--time", "5+0.1")

    whites = [matches.get(db, match_id)["white"]["name"] for match_id in ids]
    assert whites == ["Random", "Material", "Random"]
    discipline = matches.get(db, ids[0])["discipline_snapshot"]
    assert discipline["name"] == "5+0.1"
    assert (discipline["initial_time_ms"], discipline["increment_ms"]) == (5000, 100)


def store_discipline(db, name: str, *, archived: bool = False) -> dict:
    settings = Discipline(name=name, initial_time_ms=180_000, increment_ms=2000, max_moves=300)
    discipline = disciplines.new_discipline(settings, created_by=None, now=utc_now())
    discipline["archived"] = archived
    disciplines.insert(db, discipline)
    return discipline


def test_free_times_make_an_unrated_game(db, reference_bots):
    [match_id] = enqueue(db, "Random", "Material")

    match = matches.get(db, match_id)
    assert match["discipline_snapshot"]["name"] == "60+1"
    assert match["discipline_snapshot"]["discipline_id"] is None
    assert match["rated"] is False


def test_a_stored_discipline_gives_times_and_limits(db, reference_bots):
    stored = store_discipline(db, "Blitz")

    [match_id] = enqueue(db, "Random", "Material", "--discipline", "blitz")

    match = matches.get(db, match_id)
    snapshot = match["discipline_snapshot"]
    assert snapshot["discipline_id"] == stored["_id"]
    assert (snapshot["name"], snapshot["initial_time_ms"], snapshot["max_moves"]) == (
        "Blitz",
        180_000,
        300,
    )
    assert match["rated"] is True


def test_an_unknown_discipline_names_the_known_ones(db, reference_bots):
    store_discipline(db, "Blitz")
    store_discipline(db, "Old", archived=True)

    for name in ("Rapid", "Old"):
        with pytest.raises(EnqueueError, match="known: Blitz$"):
            enqueue(db, "Random", "Material", "--discipline", name)


def test_a_discipline_excludes_free_settings(db, reference_bots):
    store_discipline(db, "Blitz")

    with pytest.raises(EnqueueError, match="excludes"):
        enqueue(db, "Random", "Material", "--discipline", "Blitz", "--time", "5+0")


def test_unknown_bot_names_the_known_ones(db, reference_bots):
    with pytest.raises(EnqueueError, match="Material, Random"):
        enqueue(db, "Random", "Stockfish")


@pytest.mark.parametrize(
    "argv",
    [
        ["--fen", "not a position"],
        ["--time", "fast"],
        ["--max-moves", "0"],
        ["--games", "0"],
    ],
)
def test_invalid_settings_queue_nothing(db, reference_bots, argv):
    with pytest.raises(ValueError):
        enqueue(db, "Random", "Material", *argv)

    assert matches.page(db, {}, limit=10, offset=0)[1] == 0
