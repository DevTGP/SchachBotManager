import pytest
from sbm_store import matches

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
