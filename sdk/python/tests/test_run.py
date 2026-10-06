"""run in a real bot process: transports, protected stdout, options, data and exit codes."""

import json
import os
import socket
import subprocess
import sys
import threading

import pytest
from protocol_schemas import example, violations

import sbm

MESSAGES = [example("init.standard"), example("turn.first_move"), example("game_over.checkmate")]
REFEREE_INPUT = "".join(json.dumps(message) + "\n" for message in MESSAGES).encode()

BOT = """
import os
import sys

import sbm


class TestBot(sbm.Bot):
    def on_game_start(self, info):
        {start}

    def choose_move(self, board, clock):
        {turn}
        return board.legal_moves()[0]


sbm.run(TestBot)
"""


def write_bot(directory, start="pass", turn="pass"):
    path = directory / "my_bot.py"
    path.write_text(BOT.format(start=start, turn=turn), encoding="utf-8")
    return path


def environment(**variables):
    clean = {key: value for key, value in os.environ.items() if not key.startswith("SBM_")}
    return clean | variables


def run_bot(path, *arguments, data=REFEREE_INPUT, **variables):
    return subprocess.run(
        [sys.executable, str(path), *arguments],
        input=data,
        capture_output=True,
        env=environment(**variables),
        cwd=path.parent.parent,
        timeout=60,
    )


def answers(stdout: bytes) -> list[dict]:
    messages = [json.loads(line) for line in stdout.decode("utf-8").splitlines()]
    for message in messages:
        assert violations("bot_message", message) == []
    return messages


def test_stdout_carries_only_the_protocol(tmp_path):
    start = 'print("from print"); os.write(1, b"raw write\\n"); sys.stdout.flush()'
    process = run_bot(write_bot(tmp_path, start=start))
    assert process.returncode == 0, process.stderr
    assert [message["type"] for message in answers(process.stdout)] == ["ready", "move"]
    stderr = process.stderr.decode()
    assert "from print" in stderr
    assert "raw write" in stderr


def test_stdin_is_not_readable_by_the_bot(tmp_path):
    process = run_bot(write_bot(tmp_path, start="sbm.Log.info(repr(sys.stdin.read()))"))
    assert process.returncode == 0, process.stderr
    assert "INFO  ''" in process.stderr.decode()


def test_load_data_next_to_the_main_file(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "book.bin").write_bytes(b"opening")
    process = run_bot(write_bot(tmp_path, start='sbm.Log.info(sbm.load_data("book.bin"))'))
    assert process.returncode == 0, process.stderr
    assert "INFO  b'opening'" in process.stderr.decode()


def test_load_data_from_sbm_data_dir(tmp_path):
    (tmp_path / "server").mkdir()
    (tmp_path / "server" / "book.bin").write_bytes(b"server")
    start = 'sbm.Log.info(sbm.load_data("book.bin"))'
    process = run_bot(write_bot(tmp_path, start=start), SBM_DATA_DIR=str(tmp_path / "server"))
    assert "INFO  b'server'" in process.stderr.decode()


def test_exception_ends_the_process_with_code_1(tmp_path):
    process = run_bot(write_bot(tmp_path, turn='raise KeyError("lost")'))
    assert process.returncode == 1
    assert [message["type"] for message in answers(process.stdout)] == ["ready"]
    stderr = process.stderr.decode()
    assert "ERROR choose_move raised KeyError: 'lost'" in stderr
    assert "Traceback" in stderr
    assert "my_bot.py" in stderr


def test_protocol_error_ends_the_process_with_code_1(tmp_path):
    process = run_bot(write_bot(tmp_path), data=b"not json\n")
    assert process.returncode == 1
    assert "ERROR protocol error" in process.stderr.decode()


def test_log_level_and_file_from_arguments(tmp_path):
    log_file = tmp_path / "bot.log"
    turn = 'sbm.Log.debug("deep"); sbm.Log.trace("deeper")'
    process = run_bot(
        write_bot(tmp_path, turn=turn), "--log-level", "debug", "--log-file", log_file
    )
    assert process.returncode == 0, process.stderr
    assert "[ply 0] DEBUG deep" in process.stderr.decode()
    written = log_file.read_text("utf-8")
    assert "[ply 0] DEBUG deep" in written
    assert "deeper" not in written


def test_arguments_win_over_the_environment(tmp_path):
    turn = 'sbm.Log.info("visible")'
    path = write_bot(tmp_path, turn=turn)
    assert "visible" not in run_bot(path, SBM_LOG_LEVEL="warn").stderr.decode()
    assert "visible" in run_bot(path, "--log-level", "info", SBM_LOG_LEVEL="warn").stderr.decode()


def test_unknown_arguments_are_left_to_the_bot(tmp_path):
    start = "sbm.Log.info(sys.argv[1:])"
    process = run_bot(write_bot(tmp_path, start=start), "--depth", "4", "--log-level", "info")
    assert process.returncode == 0, process.stderr
    assert "INFO  ['--depth', '4', '--log-level', 'info']" in process.stderr.decode()


@pytest.mark.parametrize(
    ("arguments", "variables"),
    [(["--log-level", "loud"], {}), (["--tcp", "70000"], {}), ([], {"SBM_TRANSPORT": "pipe"})],
)
def test_invalid_options(tmp_path, arguments, variables):
    process = run_bot(write_bot(tmp_path), *arguments, **variables)
    assert process.returncode == 1
    assert process.stdout == b""
    assert process.stderr.decode().startswith("sbm: ")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def test_unreachable_arena(tmp_path):
    port = free_port()
    process = run_bot(write_bot(tmp_path), "--tcp", str(port))
    assert process.returncode == 1
    assert f"ERROR cannot connect to the arena on 127.0.0.1:{port}" in process.stderr.decode()


@pytest.mark.parametrize("from_environment", [False, True])
def test_tcp(tmp_path, from_environment):
    received = []

    def referee(server):
        connection, _ = server.accept()
        with connection, connection.makefile("rwb") as stream:
            for message in MESSAGES:
                stream.write(json.dumps(message).encode() + b"\n")
                stream.flush()
                if message["type"] != "game_over":
                    received.append(json.loads(stream.readline()))

    with socket.create_server(("127.0.0.1", 0)) as server:
        port = server.getsockname()[1]
        thread = threading.Thread(target=referee, args=(server,))
        thread.start()
        path = write_bot(tmp_path, start='print("still stdout")')
        if from_environment:
            process = run_bot(path, data=b"", SBM_TRANSPORT="tcp", SBM_PORT=str(port))
        else:
            process = run_bot(path, "--tcp", str(port), data=b"")
        thread.join(timeout=60)
    assert process.returncode == 0, process.stderr
    assert [message["type"] for message in received] == ["ready", "move"]
    assert process.stdout == b"still stdout\n".replace(b"\n", os.linesep.encode())


def test_run_needs_a_bot_class():
    with pytest.raises(TypeError, match="subclass of sbm.Bot"):
        sbm.run(object)
    with pytest.raises(TypeError, match="subclass of sbm.Bot"):
        sbm.run(int)
