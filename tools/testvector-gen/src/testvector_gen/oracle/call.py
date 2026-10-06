"""One call of an API function as the oracle sees it."""

from collections.abc import Callable
from dataclasses import dataclass

import chess


@dataclass
class Call:
    board: chess.Board | None
    move: int | None
    args: tuple

    def require_board(self) -> chess.Board:
        if self.board is None:
            raise ValueError("Board method without board")
        return self.board

    def require_move(self) -> int:
        if self.move is None:
            raise ValueError("Move method without move")
        return self.move


# Returns the JSON-encoded result or raises ApiError.
Handler = Callable[[Call], object]
