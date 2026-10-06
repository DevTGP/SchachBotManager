"""How a bot is given on the command line (E67).

- "tcp" or "tcp:PORT": the bot connects over TCP, e.g. from an IDE (default port 7470).
- "random" or "material": a reference bot from sbm.bots (E68); "./random" means a file.
- A .py file: runs with the Python that runs the arena, so the SDK is available.
- Anything else: a command line, e.g. "java -jar bot.jar" or "./engine".
"""

import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from sbm.options import DEFAULT_PORT
from sbm.referee.settings import MAX_NAME_LENGTH

# Short name: module of the reference bot.
REFERENCE_BOTS = {"random": "sbm.bots.random_mover", "material": "sbm.bots.material"}


class BotSpecError(ValueError):
    """The bot cannot be used as given."""


@dataclass(frozen=True)
class BotSpec:
    """name is shown in the game and in the PGN; command is None for a TCP bot."""

    name: str
    command: list[str] | str | None = None
    port: int | None = None


def parse_bot(text: str) -> BotSpec:
    if text.lower() == "tcp":
        return _tcp(DEFAULT_PORT)
    if text.lower().startswith("tcp:"):
        return _tcp(_port(text[4:]))
    if text.lower() in REFERENCE_BOTS:
        return BotSpec(text.lower(), [sys.executable, "-m", REFERENCE_BOTS[text.lower()]])
    path = Path(text)
    if path.suffix.lower() == ".py":
        if not path.is_file():
            raise BotSpecError(f"{text!r} is not a file")
        return BotSpec(_shorten(path.stem), [sys.executable, str(path)])
    if path.is_file():
        return BotSpec(_shorten(path.stem), [str(path)])
    return _command(text)


def _port(text: str) -> int:
    if not text.isdigit() or not 1 <= int(text) <= 65535:
        raise BotSpecError(f"invalid port {text!r}, expected 1 to 65535")
    return int(text)


def _tcp(port: int) -> BotSpec:
    return BotSpec(f"tcp-{port}", port=port)


def _command(text: str) -> BotSpec:
    try:
        words = shlex.split(text, posix=sys.platform != "win32")
    except ValueError as error:
        raise BotSpecError(f"cannot read the command {text!r}: {error}") from None
    if not words:
        raise BotSpecError("the bot is empty")
    # Windows passes the command line on unchanged; the program splits it itself.
    command = text if sys.platform == "win32" else words
    return BotSpec(_shorten(_name_from(words)), command)


def _name_from(words: list[str]) -> str:
    """The first word naming a file after the program, e.g. bot for "java -jar bot.jar"."""
    for word in words[1:]:
        path = Path(word.strip('"'))
        if path.suffix and path.is_file():
            return path.stem
    return Path(words[0].strip('"')).stem or words[0]


def _shorten(name: str) -> str:
    return name[:MAX_NAME_LENGTH] or "bot"


def unique_names(specs: list[BotSpec]) -> list[BotSpec]:
    """Equal names get a number, e.g. for a bot against itself; TCP ports must differ."""
    ports = [spec.port for spec in specs if spec.port is not None]
    if len(ports) != len(set(ports)):
        raise BotSpecError("two TCP bots need different ports, e.g. tcp:7470 and tcp:7471")
    names = [spec.name for spec in specs]
    result = []
    for index, spec in enumerate(specs, 1):
        if names.count(spec.name) > 1:
            suffix = f"-{index}"
            name = spec.name[: MAX_NAME_LENGTH - len(suffix)] + suffix
            spec = BotSpec(name, spec.command, spec.port)
        result.append(spec)
    return result
