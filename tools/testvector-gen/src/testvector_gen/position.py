"""The board a vector is called on, and position properties shared by several functions."""

from collections.abc import Iterable
from dataclasses import dataclass

import chess

from testvector_gen.codes import encode_move, move_parts, promotion_type
from testvector_gen.fen_rules import parse_fen

START_FEN = chess.STARTING_FEN
NULL_UCI = "0000"


@dataclass(frozen=True)
class Setup:
    """Board.from_fen(fen), then each move by UCI; 0000 is a null move."""

    fen: str = START_FEN
    moves: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {"fen": self.fen, "moves": list(self.moves)}


def setup(fen: str = START_FEN, moves: str = "") -> Setup:
    return Setup(fen, tuple(moves.split()))


def build(board_setup: Setup) -> chess.Board:
    """The board of a setup; every move must be legal and every null move allowed."""
    board = parse_fen(board_setup.fen)
    for uci in board_setup.moves:
        if uci == NULL_UCI:
            if board.is_check():
                raise ValueError(f"null move in check in setup {board_setup}")
            board.push(chess.Move.null())
            continue
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"illegal move {uci} in setup {board_setup}")
        board.push(move)
    return board


def find_move(board: chess.Board, value: int) -> chess.Move | None:
    """The legal move with the same from-square, to-square and promotion piece."""
    from_square, to_square, flags = move_parts(value)
    promotion = promotion_type(flags)
    for move in board.legal_moves:
        if (move.from_square, move.to_square, move.promotion) == (
            from_square,
            to_square,
            promotion,
        ):
            return move
    return None


def legal_en_passant_square(board: chess.Board) -> chess.Square | None:
    return board.ep_square if board.has_legal_en_passant() else None


def position_key(board: chess.Board) -> tuple:
    """Pieces, side to move, castling rights and en passant square as in fen."""
    return (board.board_fen(), board.turn, board.castling_rights, legal_en_passant_square(board))


def earlier_boards(board: chess.Board) -> Iterable[chess.Board]:
    """The board itself, then the board before each move of its history, newest first."""
    current = board.copy()
    yield current.copy()
    while current.move_stack:
        current.pop()
        yield current.copy()


def history_values(board: chess.Board) -> list[int]:
    """Complete move values of the history, oldest first."""
    boards = list(earlier_boards(board))
    moves = board.move_stack
    return [encode_move(boards[len(moves) - index], move) for index, move in enumerate(moves)]
