"""One game as Game sees it, passed to the viewer window if one is open (E106)."""

from sbm.clock import Clock
from sbm.records import GameInfo
from sbm.viewer.window import active_window


class GameView:
    """Every call does nothing without an open window."""

    def started(self, bot: str, info: GameInfo) -> None:
        if (window := active_window()) is not None:
            window.game_started(bot, info)

    def opponent_moved(self, ply: int, uci: object, fen: str, clock: Clock) -> None:
        """ply is the number of half-moves played including uci; the first turn has none."""
        if ply > 0 and isinstance(uci, str) and (window := active_window()) is not None:
            clocks = (clock.remaining_ms(), clock.opponent_remaining_ms())
            window.move_played(ply, uci, fen, by_bot=False, clocks=clocks)

    def own_move(self, ply: int, answer: dict, fen: str, clock: Clock) -> None:
        """answer is the move message sent to the referee; the bot's clock is an estimate."""
        if (window := active_window()) is None:
            return
        elapsed_ms = clock.elapsed_ms()
        remaining_ms = clock.remaining_ms() - elapsed_ms + clock.increment_ms()
        clocks = (remaining_ms, clock.opponent_remaining_ms())
        window.move_played(ply, answer["move"], fen, True, clocks, elapsed_ms, answer.get("info"))

    def ended(self, game_over: dict) -> None:
        if (window := active_window()) is not None:
            window.game_over(game_over)
