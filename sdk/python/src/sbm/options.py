"""Start options of run from the command line and the environment (E61); arguments win."""

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from sbm.constants import INFO
from sbm.log import LEVEL_NAMES

DEFAULT_PORT = 7470
TRANSPORTS = ("stdio", "tcp")


class OptionsError(ValueError):
    """An argument or environment variable has an invalid value."""


@dataclass(frozen=True)
class Options:
    transport: str = "stdio"
    port: int = DEFAULT_PORT
    log_level: int = INFO
    log_file: str | None = None


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
    return options
