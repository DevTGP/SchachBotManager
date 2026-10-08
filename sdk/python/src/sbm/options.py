"""Start options of run from the command line and the environment (E61); arguments win."""

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from sbm.constants import INFO
from sbm.log import LEVEL_NAMES

DEFAULT_PORT = 7470
TRANSPORTS = ("stdio", "tcp", "remote")
COLORS = ("white", "black", "random")
DEFAULT_TIME = "60+1"


class OptionsError(ValueError):
    """An argument or environment variable has an invalid value."""


@dataclass(frozen=True)
class RemoteOptions:
    """A game against a bot on the server (E116); time is SECONDS+INCREMENT."""

    url: str
    token: str
    opponent: str
    color: str = "random"
    discipline: str | None = None
    time: str = DEFAULT_TIME


@dataclass(frozen=True)
class Options:
    transport: str = "stdio"
    port: int = DEFAULT_PORT
    log_level: int = INFO
    log_file: str | None = None
    remote: RemoteOptions | None = None


def _port(text: str) -> int:
    if not text.isdigit() or not 1 <= int(text) <= 65535:
        raise OptionsError(f"invalid port {text!r}, expected 1 to 65535")
    return int(text)


def _level(text: str) -> int:
    name = text.upper()
    if name not in LEVEL_NAMES:
        raise OptionsError(f"invalid log level {text!r}, expected one of {', '.join(LEVEL_NAMES)}")
    return LEVEL_NAMES.index(name)


def _parser() -> argparse.ArgumentParser:
    # Unknown arguments belong to the bot, so there is neither help nor abbreviation.
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False, exit_on_error=False)
    parser.add_argument("--tcp", nargs="?", const="", default=None)
    parser.add_argument("--log-level")
    parser.add_argument("--log-file")
    for name in ("--remote", "--token", "--opponent", "--color", "--discipline", "--time"):
        parser.add_argument(name)
    return parser


def _from_environment(environ: Mapping[str, str]) -> Options:
    transport = environ.get("SBM_TRANSPORT", "stdio").lower()
    if transport not in TRANSPORTS:
        raise OptionsError(f"invalid SBM_TRANSPORT {transport!r}, expected stdio or tcp")
    port = environ.get("SBM_PORT")
    level = environ.get("SBM_LOG_LEVEL")
    return Options(
        transport=transport,
        port=DEFAULT_PORT if port is None else _port(port),
        log_level=INFO if level is None else _level(level),
        log_file=environ.get("SBM_LOG_FILE") or None,
    )


def parse_options(argv: Sequence[str], environ: Mapping[str, str]) -> Options:
    """Options for run from the arguments after the program name and the environment."""
    options = _from_environment(environ)
    try:
        arguments, _ = _parser().parse_known_args(list(argv))
    except argparse.ArgumentError as error:
        raise OptionsError(str(error)) from None
    if arguments.tcp is not None:
        port = _port(arguments.tcp) if arguments.tcp else options.port
        options = replace(options, transport="tcp", port=port)
    if arguments.log_level is not None:
        options = replace(options, log_level=_level(arguments.log_level))
    if arguments.log_file is not None:
        options = replace(options, log_file=arguments.log_file or None)
    if arguments.remote is not None:
        options = replace(options, transport="remote")
    if options.transport == "remote":
        options = replace(options, remote=_remote(arguments, environ))
    return options


def _remote(arguments: argparse.Namespace, environ: Mapping[str, str]) -> RemoteOptions:
    """The remote options; the SDK reads them only for this transport, so a bot may use the
    same argument names for itself otherwise.
    """

    def value(name: str, variable: str) -> str | None:
        given = getattr(arguments, name)
        return given if given is not None else (environ.get(variable) or None)

    url = value("remote", "SBM_REMOTE_URL")
    token = value("token", "SBM_TOKEN")
    opponent = value("opponent", "SBM_OPPONENT")
    for found, what in ((url, "--remote URL"), (token, "SBM_TOKEN"), (opponent, "--opponent")):
        if not found:
            raise OptionsError(f"a remote game needs {what}")
    color = (value("color", "SBM_COLOR") or "random").lower()
    if color not in COLORS:
        raise OptionsError(f"invalid color {color!r}, expected one of {', '.join(COLORS)}")
    return RemoteOptions(
        url=url,
        token=token,
        opponent=opponent,
        color=color,
        discipline=value("discipline", "SBM_DISCIPLINE"),
        time=value("time", "SBM_TIME") or DEFAULT_TIME,
    )
