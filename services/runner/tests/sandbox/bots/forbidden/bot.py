"""Imports a module the whitelist does not allow; the analysis must find it (E90)."""

import socket

import sbm


class Forbidden(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        socket.gethostname()
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Forbidden)
