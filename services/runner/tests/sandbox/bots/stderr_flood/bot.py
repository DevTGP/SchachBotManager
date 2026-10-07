"""Writes 32 MiB to stderr on every move and still plays (sandbox.md)."""

import sys

import sbm

BLOCK = "x" * (1 << 20)


class StderrFlood(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        for _ in range(32):
            sys.stderr.write(BLOCK)
        sys.stderr.flush()
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(StderrFlood)
