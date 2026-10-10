"""A bot named in a request body: a verified bot by id, or random (E162).

A random side is drawn anew for every game from all verified bots, never the bot on the other
side of that game.
"""

from pymongo.database import Database
from sbm_store import bot_draw, bots

from sbm_api import body
from sbm_api.errors import invalid_parameter

RANDOM = "random"


def choice(db: Database, data: dict, field: str) -> dict | None:
    """The verified bot in field, None for random."""
    if data.get(field) == RANDOM:
        return None
    return verified_bot(db, data, field)


def verified_bot(db: Database, data: dict, field: str) -> dict:
    bot = bots.get(db, body.identifier(data, field))
    if bot is None or bot["status"] != bots.VERIFIED:
        raise invalid_parameter(field, f"{field} is not a verified bot")
    return bot


def check_pool(db: Database, white: dict | None, black: dict | None, field: str) -> None:
    """Enough verified bots for the random sides, so every draw finds one."""
    fixed = [bot["_id"] for bot in (white, black) if bot is not None]
    needed = 2 - len(fixed)
    if needed and bot_draw.candidates(db, fixed) < needed:
        raise invalid_parameter(field, "there are too few verified bots to draw from")


def draw(db: Database, other: dict | None, field: str) -> dict:
    """A random bot that is not other."""
    bot = bot_draw.draw(db, [] if other is None else [other["_id"]])
    if bot is None:
        raise invalid_parameter(field, "there are too few verified bots to draw from")
    return bot


def pairings(
    db: Database, white: dict | None, black: dict | None, *, games: int, alternate: bool
) -> list[tuple[dict, dict]]:
    """White and black of each game; with alternate the sides swap before the next draw."""
    games_list = []
    for _ in range(games):
        game_white = white or draw(db, black, "white_bot_id")
        game_black = black or draw(db, game_white, "black_bot_id")
        games_list.append((game_white, game_black))
        if alternate:
            white, black = black, white
    return games_list


def label(bot: dict | None) -> str:
    """The bot's name, or random."""
    return RANDOM if bot is None else bot["name"]
