"""End of a game: result and termination code (bot-protokoll.md, match-runner.md, E44)."""

from dataclasses import dataclass

from sbm._core import Board
from sbm.constants import BLACK, WHITE

WINS = ("1-0", "0-1")
DRAW = "1/2-1/2"
NO_RESULT = "*"
COLOR_NAMES = ("White", "Black")


@dataclass(frozen=True)
class Outcome:
    """result as in PGN, termination as in game_over; winner is a color or None.

    detail explains the ending for logs and the viewer, e.g. which move was illegal.
    """

    result: str
    termination: str
    winner: int | None
    detail: str


def win(winner: int, termination: str, detail: str) -> Outcome:
    return Outcome(WINS[winner], termination, winner, detail)


def loss(loser: int, termination: str, detail: str) -> Outcome:
    return win(1 - loser, termination, f"{COLOR_NAMES[loser]}: {detail}")


def draw(termination: str, detail: str) -> Outcome:
    return Outcome(DRAW, termination, None, detail)


def position_outcome(board: Board, max_moves: int, plies: int) -> Outcome | None:
    """The ending the referee scores by itself in this position, if any.

    The rules come from the core; draws by repetition and the fifty-move rule end the game at
    once, without a claim. plies counts the half-moves played since the start position.
    """
    if board.is_checkmate():
        return win(1 - board.side_to_move(), "checkmate", "checkmate")
    if board.is_stalemate():
        return draw("stalemate", "stalemate")
    if board.is_insufficient_material():
        return draw("insufficient_material", "neither side can checkmate")
    if board.is_fifty_move_rule():
        return draw("fifty_move_rule", "50 moves without capture or pawn move")
    if board.is_repetition(3):
        return draw("threefold_repetition", "the position occurred three times")
    if plies >= 2 * max_moves:
        return draw("max_moves", f"move limit of {max_moves} moves reached")
    return None


def timeout_outcome(board: Board, loser: int) -> Outcome:
    """Loss on time, or a draw if the opponent cannot checkmate with its material."""
    winner = 1 - loser
    if board.has_insufficient_material(winner):
        return draw(
            "timeout_insufficient_material",
            f"{COLOR_NAMES[loser]} ran out of time, {COLOR_NAMES[winner]} cannot checkmate",
        )
    return loss(loser, "timeout", "ran out of time")


def startup_outcome(failures: dict[int, Outcome]) -> Outcome | None:
    """The ending if bots failed to start; both failing aborts the game without a winner."""
    if len(failures) == 2:
        details = "; ".join(failures[color].detail for color in (WHITE, BLACK))
        return Outcome(NO_RESULT, "startup_timeout", None, f"neither bot started: {details}")
    return next(iter(failures.values()), None)
