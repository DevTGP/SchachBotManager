"""Keeps a thread busy all the time; while frozen it must not get any processor time."""

import threading

import sbm


def spin() -> None:
    while True:
        pass


class Spinner(sbm.Bot):
    def on_game_start(self, info: sbm.GameInfo) -> None:
        threading.Thread(target=spin, daemon=True).start()

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Spinner)
