"""One game from the bot's side: init, turns and game_over (state machine of bot-protokoll.md)."""

import traceback
from collections.abc import Callable
from contextlib import suppress

from sbm import protocol
from sbm._core import Board, Move, core_version
from sbm.bot import Bot, take_report
from sbm.channel import Channel, ProtocolError
from sbm.clock import Clock
from sbm.errors import ChessError
from sbm.log import Log, set_ply
from sbm.records import GameInfo, GameResult
from sbm.viewer.game_view import GameView


class BotError(Exception):
    """A callback raised or returned something unusable; the process ends (E49)."""


def guarded(name: str, callback: Callable, *args: object) -> object:
    """Calls bot code and turns any exception into a BotError that keeps it as the cause."""
    try:
        return callback(*args)
    except Exception as error:
        raise BotError(f"{name} raised {type(error).__name__}: {error}") from error


def describe(error: BotError) -> str:
    """The message of a BotError with the traceback of the bot's exception, for the log."""
    cause = error.__cause__
    if cause is None:
        return str(error)
    return f"{error}\n{''.join(traceback.format_exception(cause)).rstrip()}"


class Game:
    """info and result are set once init and game_over arrive, for play to report the game."""

    def __init__(self, bot: Bot, channel: Channel) -> None:
        self._bot = bot
        self._channel = channel
        self._board: Board | None = None
        self._increment_ms = 0
        self._view = GameView()
        self.info: GameInfo | None = None
        self.result: GameResult | None = None

    def play(self) -> None:
        """Answers referee messages until game_over or the end of the input."""
        while (message := self._channel.receive()) is not None:
            kind = message.get("type")
            if kind == "init":
                self._start(message)
            elif kind == "turn":
                self._turn(message)
            elif kind == "error":
                Log.error(f"referee reports {message.get('code')}: {message.get('message')}")
            elif kind == "game_over":
                self._end(message)
                return
            else:
                Log.warn(f"ignoring a message of unknown type {kind!r}")
        Log.warn("input ended before game_over")

    def _start(self, init: dict) -> None:
        if self._board is not None:
            raise ProtocolError("init: second init in one game")
        info = protocol.game_info(init)
        self.info = info
        try:
            self._board = Board.from_fen(info.start_fen)
        except ChessError as error:
            raise ProtocolError(f"init: {error}") from None
        self._increment_ms = info.increment_ms
        supported = protocol.supported_versions(init)
        if protocol.PROTOCOL_VERSION not in supported:
            # The referee diagnoses the mismatch after ready; this line tells the author why.
            Log.error(
                f"the referee supports protocol versions {supported}, "
                f"this SDK speaks version {protocol.PROTOCOL_VERSION}; update the SDK"
            )
        guarded("on_game_start", self._bot.on_game_start, info)
        self._view.started(type(self._bot).__name__, info)
        self._channel.send(protocol.ready(core_version()))

    def _turn(self, turn: dict) -> None:
        # First, so that elapsed_ms covers everything the SDK does in this turn.
        clock = Clock(
            protocol.field(turn, "remaining_ms", int),
            protocol.field(turn, "opponent_remaining_ms", int),
            self._increment_ms,
        )
        if self._board is None:
            raise ProtocolError("turn before init")
        ply = protocol.field(turn, "ply", int)
        set_ply(ply)
        self._synchronize(turn)
        self._view.opponent_moved(ply, turn.get("last_move"), self._board.fen(), clock)
        take_report(self._bot)
        choice = guarded("choose_move", self._bot.choose_move, self._board.copy(), clock)
        answer = self._answer(choice)
        self._channel.send(answer)
        if choice != Move.RESIGN and self._play_own(choice):
            self._view.own_move(ply + 1, answer, self._board.fen(), clock)

    def _synchronize(self, turn: dict) -> None:
        """Applies the opponent's move and adopts the referee's position on a mismatch (E42)."""
        fen = protocol.field(turn, "fen", str)
        try:
            # Read and written again, so an en passant square without a legal capture still
            # compares equal (E48).
            reference = Board.from_fen(fen)
        except ChessError as error:
            raise ProtocolError(f"turn: {error}") from None
        last_move = turn.get("last_move")
        if last_move is not None:
            # A move that does not fit is repaired by the comparison below.
            with suppress(ChessError, TypeError):
                self._board.make_move(self._board.parse_move(last_move))
        if self._board.fen() != reference.fen():
            Log.warn(f"own position differs from the referee's; continuing from {fen}")
            self._board = reference

    def _answer(self, choice: object) -> dict:
        if not isinstance(choice, Move):
            raise BotError(f"choose_move returned {type(choice).__name__}, not a Move")
        info = take_report(self._bot)
        if choice == Move.RESIGN:
            return protocol.resign()
        try:
            uci = choice.uci()
        except ChessError:
            raise BotError(f"choose_move returned {choice!r}, which has no UCI form") from None
        return protocol.move(uci, info)

    def _play_own(self, choice: Move) -> bool:
        try:
            self._board.make_move(choice)
        except ChessError:
            Log.warn(f"own move {choice.uci()} is not legal in this position; the referee decides")
            return False
        return True

    def _end(self, game_over: dict) -> None:
        result = protocol.game_result(game_over)
        self.result = result
        # First, so that the window shows the result even if on_game_end raises.
        self._view.ended(game_over)
        guarded("on_game_end", self._bot.on_game_end, result)
