"""An uploaded bot as the verification sees it: an own module and a data file (E94)."""

import sbm
from opening import first_move


class Uploaded(sbm.Bot):
    def __init__(self) -> None:
        self.book = sbm.load_data("book.txt").decode().split()

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return first_move(board, self.book)


if __name__ == "__main__":
    sbm.run(Uploaded)
