"""Bot SDK of SchachBotManager (spec/api/): board and moves, the bot base class, run and play."""

from sbm import constants
from sbm._core import Board, Move, core_version
from sbm.bot import Bot
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
from sbm.records import GameInfo, GameResult, Info, PlayedGame
from sbm.runtime import run
from sbm.starter import play

__version__ = core_version()

__all__ = [
    "Board",
    "Bot",
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
    "PlayedGame",
    "__version__",
    "load_data",
    "play",
    "run",
]
__all__ += constants.__all__
