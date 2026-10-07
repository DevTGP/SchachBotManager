"""Fills 2 GiB, twice its limit; exits with 42 if it is still alive (sandbox.md)."""

import os

import sbm

CHUNK = 64 << 20


class Memory(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        # Multiplying writes every byte, so the pages are really used.
        self.chunks = [b"\x01" * CHUNK for _ in range((2 << 30) // CHUNK)]
        os._exit(42)


if __name__ == "__main__":
    sbm.run(Memory)
