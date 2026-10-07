"""Players for the reference bots, the only bots that run without a sandbox (E72)."""

import sys

from sbm.arena.process_player import ProcessPlayer
from sbm.referee import Player
from sbm_store import bots

# Modules below sbm.bots that may run; anything else waits for the sandbox in M3.
BUILTIN_MODULES = frozenset({"random_mover", "material"})


class UnsupportedBot(Exception):
    """The bot cannot run on this server; the match is aborted, not retried."""


def builtin_player(bot: dict) -> Player:
    module = bots.builtin_module(bot)
    if module not in BUILTIN_MODULES:
        raise UnsupportedBot(f"bot {bot['_id']} needs the sandbox, which comes with M3 (E72)")
    # The reference bots log nothing worth keeping; their stderr is dropped.
    return ProcessPlayer(bot["name"], [sys.executable, "-m", f"sbm.bots.{module}"], log=None)
