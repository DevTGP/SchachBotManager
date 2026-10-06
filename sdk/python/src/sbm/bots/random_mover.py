"""Plays a random legal move: the weakest possible opponent and the shortest complete bot."""

import random

import sbm


class RandomMover(sbm.Bot):
    def __init__(self) -> None:
        self.random = random.Random()

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return self.random.choice(board.legal_moves())


if __name__ == "__main__":
    sbm.run(RandomMover)
