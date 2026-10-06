"""Games between bots in real processes, over pipes and over TCP."""

import io
import subprocess
import sys
import threading

from arena_bots import CRASH_AFTER_READY, FIRST_MOVE, GAP_REPORTER, SLOW, write_bot

from sbm.arena.process_player import ProcessPlayer
from sbm.arena.tcp_player import TcpListener, connect
from sbm.referee import Match, MatchSettings


def python(path) -> list[str]:
    return [sys.executable, str(path)]


def play(white, black, **settings):
    settings = MatchSettings(**({"initial_time_ms": 20_000, "max_moves": 3} | settings))
    return Match(white, black, settings).play()


def test_game_over_pipes_with_log(tmp_path):
    bot = write_bot(tmp_path, "first", FIRST_MOVE)
    log = io.StringIO()
    record = play(ProcessPlayer("w", python(bot), log=log), ProcessPlayer("b", python(bot)))
    assert record.outcome.termination == "max_moves"
    assert record.white.sdk is not None and record.white.lang == "python"
    assert len(record.moves) == 6
    assert "[w] " in log.getvalue() and "thinking" in log.getvalue()


def test_crash_reports_exit_code(tmp_path):
    crash = write_bot(tmp_path, "crash", CRASH_AFTER_READY)
    first = write_bot(tmp_path, "first", FIRST_MOVE)
    record = play(ProcessPlayer("w", python(crash), log=None), ProcessPlayer("b", python(first)))
    assert (record.outcome.result, record.outcome.termination) == ("0-1", "crash")
    assert "exited with code 3" in record.outcome.detail


def test_missing_program_is_a_crash(tmp_path):
    first = write_bot(tmp_path, "first", FIRST_MOVE)
    missing = [str(tmp_path / "no-such-program.exe")]
    record = play(ProcessPlayer("w", missing), ProcessPlayer("b", python(first)))
    assert record.outcome.winner == 1
    assert "cannot start" in record.outcome.detail


def test_frozen_outside_own_turn(tmp_path):
    gaps = write_bot(tmp_path, "gaps", GAP_REPORTER)
    slow = write_bot(tmp_path, "slow", SLOW)
    warnings = []
    white = ProcessPlayer("gaps", python(gaps), warn=warnings.append)
    record = play(white, ProcessPlayer("slow", python(slow)), max_moves=4)
    assert warnings == []
    reported = [float(move.info["text"]) for move in record.moves[::2]]
    # The slow bot thinks 0.3 s per move; the frozen bot's thread misses all of it.
    assert max(reported) >= 0.25, reported


def test_tcp_bot(tmp_path):
    bot = write_bot(tmp_path, "first", FIRST_MOVE)
    listener = TcpListener(0)
    announced = []
    process = subprocess.Popen([*python(bot), "--tcp", str(listener.port)])
    try:
        connected = {}

        def accept():
            connected["player"] = connect("remote", listener, announced.append)

        thread = threading.Thread(target=accept)
        thread.start()
        thread.join(30)
        record = play(connected["player"], ProcessPlayer("local", python(bot)))
        assert record.outcome.termination == "max_moves"
        assert record.white.name == "remote"
        assert process.wait(10) == 0
    finally:
        listener.close()
        if process.poll() is None:
            process.kill()
    assert announced == [
        f"waiting for remote to connect on 127.0.0.1:{listener.port}, e.g. --tcp {listener.port}"
    ]
