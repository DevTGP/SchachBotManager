"""Who may do what with a bot beyond reading it (E15, E95, E97)."""

from sbm_api.bot_view import may_see, may_see_details
from sbm_api.errors import forbidden, not_found


def visible_bot(bot: dict | None, viewer: dict | None) -> dict:
    """The bot if the viewer may see it at all; others learn nothing of hidden bots."""
    if bot is None or not may_see(bot, viewer):
        raise not_found("no such bot")
    return bot


def owned_bot(bot: dict | None, user: dict) -> dict:
    """The bot if it belongs to user; admins change bots through /admin/bots."""
    bot = visible_bot(bot, user)
    if bot.get("owner_id") != user["_id"]:
        raise forbidden("only the owner may change this bot")
    return bot


def source_bot(bot: dict | None, user: dict) -> dict:
    """The bot if user may read its files: the owner and admins (E97)."""
    bot = visible_bot(bot, user)
    if not may_see_details(bot, user):
        raise forbidden("only the owner and admins may read the files")
    return bot
