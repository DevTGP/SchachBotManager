"""One game from init to game_over (match-runner.md, bot-protokoll.md).

The referee owns the authoritative board, the clock and the result. Players only carry lines;
everything they send is checked strictly before it counts.
"""

import contextlib
import time
from collections.abc import Callable

from sbm._core import Board
from sbm.constants import BLACK, WHITE
from sbm.errors import ChessError
from sbm.referee import bot_messages, referee_messages
from sbm.referee.bot_messages import MoveMessage, Ready, Resign, Violation
from sbm.referee.clock import NANOSECONDS_PER_MS, GameClock, elapsed_ms
from sbm.referee.outcome import (
    Outcome,
    loss,
    position_outcome,
    startup_outcome,
    timeout_outcome,
)
from sbm.referee.player import MAX_LINE_BYTES, LineTooLong, Player, PlayerClosed, PlayerTimeout
from sbm.referee.record import MatchRecord, MoveRecord, SideRecord
from sbm.referee.settings import MatchSettings, check_name

COLOR_NAMES = referee_messages.COLOR_NAMES


class Match:
    """Plays one game between two players; play() may be called once.

    now returns monotonic nanoseconds and is replaceable for tests. on_move is called after each
    accepted move, e.g. to record the game while it runs.
    """

    def __init__(
        self,
        white: Player,
        black: Player,
        settings: MatchSettings,
        *,
        now: Callable[[], int] = time.monotonic_ns,
        on_move: Callable[[MoveRecord], None] | None = None,
    ) -> None:
        for color, player in ((WHITE, white), (BLACK, black)):
            check_name(f"{COLOR_NAMES[color]} name", player.name)
        self._players = (white, black)
        self._settings = settings
        self._now = now
        self._on_move = on_move
        self._board = Board.from_fen(settings.start_fen)
        self._clock = GameClock(settings)
        self._sides = [SideRecord(white.name), SideRecord(black.name)]
        self._moves: list[MoveRecord] = []
        # Sides that get no game_over: gone, or stopped hard after running out of time.
        self._silent: set[int] = set()
        self._played = False

    def play(self) -> MatchRecord:
        """Runs the game to its end. Exceptions other than the player ones are infrastructure
        errors: they propagate after both players are closed, and the game does not count.
        """
        if self._played:
            raise RuntimeError("a match can be played only once")
        self._played = True
        try:
            outcome = self._start_sides() or self._position_outcome()
            while outcome is None:
                outcome = self._turn()
            self._announce(outcome)
        finally:
            self._close()
        return MatchRecord(
            start_fen=self._settings.start_fen,
            white=self._sides[WHITE],
            black=self._sides[BLACK],
            moves=list(self._moves),
            outcome=outcome,
        )

    # Startup

    def _start_sides(self) -> Outcome | None:
        """Starts white, then black, so only one bot uses the processor at a time."""
        failures = {}
        for color in (WHITE, BLACK):
            failure = self._start_side(color)
            if failure is not None:
                failures[color] = failure
        return startup_outcome(failures)

    def _start_side(self, color: int) -> Outcome | None:
        player = self._players[color]
        startup_ms = self._settings.startup_ms
        start = self._now()
        deadline = start + startup_ms * NANOSECONDS_PER_MS if self._clock.running else None
        try:
            player.start()
            player.send(referee_messages.init(self._settings, color, self._players[1 - color].name))
            line = player.receive(deadline)
        except PlayerTimeout:
            return self._startup_timeout(color)
        except PlayerClosed as error:
            return self._gone(color, error)
        except LineTooLong:
            player.suspend()
            return self._violation(color, _line_too_long())
        if self._clock.running and elapsed_ms(start, self._now()) > startup_ms:
            return self._startup_timeout(color)
        player.suspend()
        try:
            message = bot_messages.read(line)
        except Violation as violation:
            return self._violation(color, violation)
        if not isinstance(message, Ready):
            return self._violation(
                color, Violation("unexpected_message", "the first message must be ready")
            )
        self._sides[color] = SideRecord(player.name, message.sdk, message.lang)
        return None

    def _startup_timeout(self, color: int) -> Outcome:
        # Frozen at once, so it cannot take the processor from the other side's startup.
        self._players[color].suspend()
        self._silent.add(color)
        return loss(color, "startup_timeout", f"no ready within {self._settings.startup_ms} ms")

    # Turns

    def _turn(self) -> Outcome | None:
        color = self._board.side_to_move()
        player = self._players[color]
        try:
            player.resume()
            early = self._reject_waiting_line(color)
            if early is not None:
                return early
            player.send(self._turn_message(color))
            start = self._now()
            line = player.receive(self._clock.deadline_ns(color, start))
            spent = elapsed_ms(start, self._now())
        except PlayerTimeout:
            return self._timeout(color)
        except PlayerClosed as error:
            return self._gone(color, error)
        except LineTooLong:
            player.suspend()
            return self._violation(color, _line_too_long())
        if self._clock.is_over(color, spent):
            return self._timeout(color)
        player.suspend()
        try:
            message = bot_messages.read(line)
        except Violation as violation:
            return self._violation(color, violation)
        if isinstance(message, Resign):
            return loss(color, "resignation", "resigned")
        if not isinstance(message, MoveMessage):
            return self._violation(
                color, Violation("unexpected_message", "expected move or resign")
            )
        return self._make_move(color, message, spent)

    def _reject_waiting_line(self, color: int) -> Outcome | None:
        """A line sent outside the own turn breaks the protocol (only possible over tcp)."""
        try:
            self._players[color].receive(self._now())
        except PlayerTimeout:
            return None
        except LineTooLong:
            pass
        self._players[color].suspend()
        return self._violation(
            color, Violation("unexpected_message", "a message arrived before turn")
        )

    def _turn_message(self, color: int) -> dict:
        return referee_messages.turn(
            last_move=self._moves[-1].uci if self._moves else None,
            fen=self._board.fen(),
            ply=len(self._moves),
            remaining_ms=self._clock.remaining_ms(color),
            opponent_remaining_ms=self._clock.remaining_ms(1 - color),
        )

    def _make_move(self, color: int, message: MoveMessage, spent: int) -> Outcome | None:
        try:
            move = self._board.parse_move(message.uci)
        except ChessError:
            violation = Violation("illegal_move", f"{message.uci} is not legal in this position")
            return self._violation(color, violation, termination="illegal_move")
        san = self._board.san(move)
        self._board.make_move(move)
        self._clock.charge(color, spent)
        record = MoveRecord(
            ply=len(self._moves) + 1,
            uci=message.uci,
            san=san,
            fen=self._board.fen(),
            elapsed_ms=spent,
            remaining_ms=self._clock.remaining_ms(color),
            info=message.info,
        )
        self._moves.append(record)
        if self._on_move is not None:
            self._on_move(record)
        return self._position_outcome()

    def _position_outcome(self) -> Outcome | None:
        return position_outcome(self._board, self._settings.max_moves, len(self._moves))

    def _timeout(self, color: int) -> Outcome:
        self._clock.flag(color)
        self._silent.add(color)
        return timeout_outcome(self._board, color)

    # Failures and the end

    def _gone(self, color: int, error: PlayerClosed) -> Outcome:
        self._silent.add(color)
        return loss(color, error.termination, f"left the game: {error}")

    def _violation(
        self, color: int, violation: Violation, termination: str = "protocol_violation"
    ) -> Outcome:
        """Tells the side what it did wrong; game_over follows at the end."""
        self._send(color, referee_messages.error(violation.code, violation.message))
        return loss(color, termination, f"{violation.code}: {violation.message}")

    def _announce(self, outcome: Outcome) -> None:
        for color in (WHITE, BLACK):
            if color in self._silent:
                continue
            with contextlib.suppress(PlayerClosed):
                self._players[color].resume()
            self._send(color, referee_messages.game_over(outcome.result, outcome.termination))

    def _send(self, color: int, message: dict) -> None:
        if color in self._silent:
            return
        try:
            self._players[color].send(message)
        except PlayerClosed:
            self._silent.add(color)

    def _close(self) -> None:
        """Closes both players even if one of them fails to close."""
        with contextlib.ExitStack() as stack:
            for player in self._players:
                stack.callback(player.close)


def _line_too_long() -> Violation:
    return Violation("line_too_long", f"a line is longer than {MAX_LINE_BYTES} bytes")
