"""Bot SDK of SchachBotManager: board, moves, constants and errors (spec/api/)."""

from sbm import constants
from sbm._core import Board, Move, core_version
from sbm.constants import *  # noqa: F403
from sbm.errors import (
    ChessError,
    DataNotFoundError,
    IllegalMoveError,
    InvalidArgumentError,
    InvalidFenError,
    InvalidStateError,
    InvalidUciError,
)

__version__ = core_version()

__all__ = [
    "Board",
    "ChessError",
    "DataNotFoundError",
    "IllegalMoveError",
    "InvalidArgumentError",
    "InvalidFenError",
    "InvalidStateError",
    "InvalidUciError",
    "Move",
    "__version__",
]
__all__ += constants.__all__
