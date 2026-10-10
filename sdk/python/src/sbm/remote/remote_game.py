"""One remote game for play (E120): open it, play it, report it."""

import time

from sbm.bot import Bot
from sbm.constants import BLACK, WHITE
from sbm.game import Game, guarded
from sbm.options import RemoteOptions
from sbm.records import PlayedGame
from sbm.remote.channel import RemoteChannel
from sbm.remote.game_request import RemoteError, Seat
from sbm.remote.opening import open_game

# The server allows one running game per token; the previous one may still be ending.
BUSY_CODE = "too_many_games"
BUSY_WAIT_SECONDS = 2.0
BUSY_ATTEMPTS = 15


def open_when_free(remote: RemoteOptions) -> tuple[Seat, RemoteChannel]:
    """open_game, waiting up to half a minute while the previous game ends on the server."""
    attempt = 1
    while True:
        try:
            return open_game(remote)
        except RemoteError as error:
            if error.code != BUSY_CODE or attempt == BUSY_ATTEMPTS:
                raise
        attempt += 1
        time.sleep(BUSY_WAIT_SECONDS)


def play_remote(bot: type[Bot], remote: RemoteOptions) -> PlayedGame:
    """Raises RemoteError, BotError or ProtocolError like run's remote transport."""
    seat, channel = open_when_free(remote)
    with channel:
        game = Game(guarded(f"{bot.__name__}()", bot), channel)
        game.play()
    if game.info is not None:
        color, opponent = game.info.color, game.info.opponent_name
    else:
        color, opponent = (WHITE if seat.color == "white" else BLACK), remote.opponent
    if game.result is None:
        # The connection ended before game_over; the site shows how the server scored it.
        return PlayedGame(seat.match_id, color, opponent, "*", "aborted")
    return PlayedGame(seat.match_id, color, opponent, game.result.result, game.result.termination)
