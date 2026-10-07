"""Never answers: loses on time and is killed afterwards (sandbox.md)."""

import sbm


class EndlessLoop(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        while True:
            pass


if __name__ == "__main__":
    sbm.run(EndlessLoop)
