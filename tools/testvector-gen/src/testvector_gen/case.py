"""Inputs of one call vector. The expected outcome comes from the oracle, not from the case."""

from dataclasses import dataclass

import chess

from testvector_gen.codes import encode_move
from testvector_gen.oracle.move import parse_uci
from testvector_gen.position import Setup, build, find_move


@dataclass(frozen=True)
class Raises:
    """Expected API error, used as `Case.expect`."""

    error: str


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()


@dataclass(frozen=True)
class Case:
    """`id` is unique within its file; the generator prefixes the file.

    `expect` guards the intent of a case: if set, the oracle must compute exactly this result or
    `Raises(error)`, otherwise generation fails.
    """

    id: str
    function: str
    args: tuple = ()
    board: Setup | None = None
    move: int | None = None
    note: str | None = None
    expect: object = UNSET


def square(name: str) -> int:
    return chess.parse_square(name)


def parsed(uci: str) -> int:
    """Value of Move.parse: from-square, to-square and promotion flags only."""
    return parse_uci(uci)


def full(board_setup: Setup, uci: str) -> int:
    """Complete value of a legal move on the board of a setup, as Board.parse_move gives it."""
    board = build(board_setup)
    move = find_move(board, parse_uci(uci))
    if move is None:
        raise ValueError(f"{uci} is not legal in {board_setup}")
    return encode_move(board, move)
