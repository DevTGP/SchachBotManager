"""Bot SDK of SchachBotManager (spec/api/): board, moves, clock, log and data files."""

from sbm import constants
from sbm._core import Board, Move, core_version
from sbm.clock import Clock
from sbm.constants import *  # noqa: F403
from sbm.data import load_data
from sbm.errors import (
    ChessError,
    DataNotFoundError,
    IllegalMoveError,
    InvalidArgumentError,
    InvalidFenError,
    InvalidStateError,
    InvalidUciError,
)
from sbm.log import Log
from sbm.records import GameInfo, GameResult, Info

__version__ = core_version()

__all__ = [
    "Board",
    "ChessError",
    "Clock",
    "DataNotFoundError",
    "GameInfo",
    "GameResult",
    "IllegalMoveError",
    "Info",
    "InvalidArgumentError",
    "InvalidFenError",
    "InvalidStateError",
    "InvalidUciError",
    "Log",
    "Move",
    "__version__",
    "load_data",
]
__all__ += constants.__all__
