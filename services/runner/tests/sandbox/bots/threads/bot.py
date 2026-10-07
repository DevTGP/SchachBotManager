"""Starts threads until the process limit stops it; exits with 42 at 200 (sandbox.md)."""

import os
import threading

import sbm

ENOUGH = 200


class Threads(sbm.Bot):
    def on_game_start(self, info: sbm.GameInfo) -> None:
        self.stop = threading.Event()
        started = 0
        try:
            while started < ENOUGH:
                threading.Thread(target=self.stop.wait, daemon=True).start()
                started += 1
        except RuntimeError:
            pass
        if started >= ENOUGH:
            os._exit(42)
        sbm.Log.info(f"{started} threads")

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Threads)
