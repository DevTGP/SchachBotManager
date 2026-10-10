"""Which bots the runner can run, and the player for a bot without the sandbox (E72, E86)."""

import sys
from collections.abc import Callable

from sbm.arena.process_player import ProcessPlayer
from sbm.referee import Player
from sbm_store import bots

# Creates the player of a stored bot; raises UnsupportedBot.
PlayerFactory = Callable[[dict], Player]

# Modules below sbm.bots that may run; no other code of the runner's own package runs as a bot.
BUILTIN_MODULES = frozenset({"random_mover", "material"})


class UnsupportedBot(Exception):
    """The bot cannot run on this server; the match is aborted, not retried."""


def reference_module(bot: dict) -> str | None:
    """The module of a reference bot, None for an uploaded bot."""
    module = bots.builtin_module(bot)
    if module is not None and module not in BUILTIN_MODULES:
        raise UnsupportedBot(f"bot {bot['_id']} refers to the unknown reference bot {module!r}")
    return module


def plain_player(bot: dict) -> Player:
    """Without a sandbox (SBM_SANDBOX=none) only the reference bots run, as plain processes."""
    module = reference_module(bot)
    if module is None:
        raise UnsupportedBot(f"bot {bot['_id']} needs the sandbox, and this runner has none")
    # The reference bots log nothing worth keeping; their stderr is dropped.
    return PlainPlayer(bot["name"], [sys.executable, "-m", f"sbm.bots.{module}"], log=None)


class PlainPlayer(ProcessPlayer):
    """stop kills the bot from another thread when the match is cancelled (E152); a bot started
    after that is killed at once. Only the process: the reference bots start no others, and
    close ends the group."""

    _stopping = False

    def start(self) -> None:
        super().start()
        if self._stopping:
            self._kill_process()

    def stop(self) -> None:
        self._stopping = True
        self._kill_process()

    def _kill_process(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            process.kill()
