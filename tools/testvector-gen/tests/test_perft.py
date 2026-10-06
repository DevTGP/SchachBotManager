from testvector_gen import perft
from testvector_gen.position import START_FEN


def test_count():
    assert perft.count(START_FEN, 3) == 8902
    assert perft.count(START_FEN, 3, "e2e4") == 600


def test_tasks_split_root_moves():
    tasks = perft._tasks({"fen": START_FEN, "depth": 3})
    assert len(tasks) == 20
    assert sum(perft.count(*task) for task in tasks) == 8902
    assert perft._tasks({"fen": START_FEN, "depth": 1}) == [(START_FEN, 1, None)]


def test_slow_marker():
    vectors = {vector["id"]: vector for vector in perft.vectors()}
    assert "slow" not in vectors["perft.start.d5"]
    assert vectors["perft.start.d6"]["slow"] is True


def test_verify_small_vectors():
    assert perft.verify(10_000) == []
