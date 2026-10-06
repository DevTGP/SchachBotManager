"""The start position from a recorded game: the position after some of its half-moves (E69).

Only the position is passed on; repetitions before it do not count in the new game.
"""

from sbm import WHITE, Board, Move
from sbm.arena.pgn_reader import PgnGame, read_games
from sbm.errors import ChessError


class ReplayError(ValueError):
    """The game cannot be replayed as asked."""


def replay_fen(pgn: str, game_number: int = 1, plies: int | None = None) -> str:
    """FEN after the first plies half-moves of a game (all of them by default)."""
    games = read_games(pgn)
    if not 1 <= game_number <= len(games):
        raise ReplayError(f"there is no game {game_number}, the PGN has {len(games)}")
    game = games[game_number - 1]
    if plies is None:
        plies = len(game.moves)
    elif plies > len(game.moves):
        raise ReplayError(f"game {game_number} has only {len(game.moves)} half-moves")
    board = _start_board(game)
    for san in game.moves[:plies]:
        board.make_move(_find_move(board, san))
    if not board.legal_moves():
        raise ReplayError(f"game {game_number} is over after {plies} half-moves")
    return board.fen()


def _start_board(game: PgnGame) -> Board:
    variant = game.tags.get("Variant", "Standard")
    if variant.lower() not in ("standard", "chess"):
        raise ReplayError(f"variant {variant!r} is not supported")
    if "FEN" not in game.tags:
        return Board()
    try:
        return Board.from_fen(game.tags["FEN"])
    except ChessError as error:
        raise ReplayError(f"FEN tag: {error}") from None


def _find_move(board: Board, san: str) -> Move:
    # The core writes SAN; reading it back by comparison keeps the rules in the core.
    wanted = _plain(san)
    for move in board.legal_moves():
        if _plain(board.san(move)) == wanted:
            return move
    number = board.fullmove_number()
    label = f"{number}. {san}" if board.side_to_move() == WHITE else f"{number}... {san}"
    raise ReplayError(f"{label} is not a legal move in {board.fen()}")


def _plain(san: str) -> str:
    """Without check marks and annotations; 0-0 written with zeros counts as O-O."""
    return san.rstrip("+#!?").replace("0", "O")
