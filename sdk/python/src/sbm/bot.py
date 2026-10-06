"""Bot: the base class the bot author extends (spec/api/bot.json)."""

from abc import ABC, abstractmethod

from sbm._core import Board, Move
from sbm.clock import Clock
from sbm.records import GameInfo, GameResult, Info


class Bot(ABC):
    """Override choose_move, optionally on_game_start and on_game_end; start with sbm.run.

    Fields of the object keep their values from turn to turn.
    """

    def on_game_start(self, info: GameInfo) -> None:  # noqa: B027 (optional callback)
        """Called once before the first turn, within the start-up budget."""

    @abstractmethod
    def choose_move(self, board: Board, clock: Clock) -> Move:
        """The move to play in the position on board, or Move.RESIGN.

        The bot may make and undo moves on board freely; the SDK keeps its own game position.
        """

    def on_game_end(self, result: GameResult) -> None:  # noqa: B027 (optional callback)
        """Called after game_over for cleanup and last log lines."""

    def report(self, info: Info) -> None:
        """Sets the search information sent with the move of the current turn."""
        if not isinstance(info, Info):
            raise TypeError(f"Bot.report: info must be an Info, not {type(info).__name__}")
        self._sbm_info = info


def take_report(bot: Bot) -> Info | None:
    """The info reported during the turn; nothing carries over to the next one."""
    info = getattr(bot, "_sbm_info", None)
    bot._sbm_info = None
    return info
