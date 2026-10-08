import json

from sbm_runner.play.human_player import HumanPlayer

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class Connection:
    def __init__(self) -> None:
        self.on_present = None
        self.lines: list[dict] = []

    def send_line(self, line: str) -> None:
        self.lines.append(json.loads(line))


class Clock:
    def __init__(self) -> None:
        self.seconds = 100.0

    def __call__(self) -> float:
        return self.seconds


def started(color: str = "white"):
    connection, clock = Connection(), Clock()
    player = HumanPlayer("alice", connection, absent_grace=60, monotonic=clock)
    init = {
        "type": "init",
        "color": color,
        "opponent_name": "Random",
        "start_fen": START,
        "initial_time_ms": 60_000,
        "increment_ms": 0,
    }
    player.send(init)
    return player, connection, clock


def test_a_browser_that_comes_back_sees_the_running_clock_counted_down():
    player, connection, clock = started()
    player.send(
        {"type": "turn", "fen": START, "remaining_ms": 58_000, "opponent_remaining_ms": 59_000}
    )

    clock.seconds += 12.5
    connection.on_present()

    sent, again = connection.lines[-2], connection.lines[-1]
    assert sent["clock"] == {"white": 58_000, "black": 59_000}
    assert again["clock"] == {"white": 45_500, "black": 59_000}
    assert {**again, "clock": sent["clock"]} == sent


def test_the_clock_of_a_browser_that_comes_back_stops_at_zero():
    player, connection, clock = started()

    clock.seconds += 90
    connection.on_present()

    assert connection.lines[-1]["clock"] == {"white": 0, "black": 60_000}


def test_a_finished_game_comes_back_unchanged():
    player, connection, clock = started()
    player.send({"type": "game_over", "result": "0-1", "termination": "resignation"})

    clock.seconds += 30
    connection.on_present()

    assert connection.lines[-1] == connection.lines[-2]
    assert connection.lines[-1]["running"] is None
