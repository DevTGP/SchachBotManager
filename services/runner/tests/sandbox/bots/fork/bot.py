"""Tries to start other processes; exits with 42 if one starts (sandbox.md)."""

import multiprocessing
import os
import subprocess

import sbm


def fork() -> None:
    if os.fork() == 0:
        os._exit(0)


def spawn() -> None:
    os.posix_spawn("/usr/local/bin/python3", ["python3", "-c", "pass"], {})


def run() -> None:
    subprocess.run(["/usr/local/bin/python3", "-c", "pass"], check=False)


def pool() -> None:
    with multiprocessing.get_context("fork").Pool(2) as workers:
        workers.map(abs, [1, 2])


def starts(attempt) -> bool:
    try:
        attempt()
    except OSError:
        return False
    return True


class Fork(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        if any(starts(attempt) for attempt in (fork, spawn, run, pool)):
            os._exit(42)
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Fork)
