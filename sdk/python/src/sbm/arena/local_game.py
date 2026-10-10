"""One local game for play (E120): the own bot in a thread against a bot process."""

from dataclasses import replace

from sbm.arena.bot_spec import BotSpec
from sbm.arena.process_player import ProcessPlayer
from sbm.arena.thread_player import ThreadPlayer
from sbm.bot import Bot
from sbm.constants import WHITE
from sbm.records import PlayedGame
from sbm.referee import Match, MatchSettings


def play_local(
    bot: type[Bot], name: str, opponent: BotSpec, color: int, settings: MatchSettings, number: int
) -> PlayedGame:
    """Raises the BotError or ProtocolError that ended the own bot's side, after the game."""
    own = ThreadPlayer(name, bot)
    # The opponent's log would mix with the own one; the arena shows it if needed.
    other = ProcessPlayer(opponent.name, opponent.command, log=None)
    white, black = (own, other) if color == WHITE else (other, own)
    settings = replace(settings, game_id=f"{settings.game_id}-{number}")
    outcome = Match(white, black, settings).play().outcome
    if own.error is not None:
        raise own.error
    return PlayedGame(settings.game_id, color, opponent.name, outcome.result, outcome.termination)
