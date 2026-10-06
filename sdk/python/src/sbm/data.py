"""load_data: the data files uploaded with the bot (spec/api/runtime.json, E30, E62)."""

import os
import sys
from pathlib import Path

from sbm.errors import DataNotFoundError, InvalidArgumentError

DATA_DIR_VARIABLE = "SBM_DATA_DIR"


def data_directory() -> Path:
    """SBM_DATA_DIR if set (server), otherwise the directory data next to the main file."""
    configured = os.environ.get(DATA_DIR_VARIABLE)
    if configured:
        return Path(configured)
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    base = Path(main_file).resolve().parent if main_file else Path.cwd()
    return base / "data"


def _is_plain_name(name: str) -> bool:
    if name in ("", ".", "..") or any(character in name for character in "/\\\0"):
        return False
    # Catches what the platform reads as a path anyway, e.g. the drive in C:book.bin on Windows.
    return os.path.basename(name) == name and not os.path.splitdrive(name)[0]


def load_data(name: str) -> bytes:
    """Contents of the data file with this name; the only way for a bot to read files."""
    if not isinstance(name, str):
        raise TypeError(f"load_data: name must be a str, not {type(name).__name__}")
    if not _is_plain_name(name):
        raise InvalidArgumentError(f"load_data: {name!r} is not a plain file name")
    directory = data_directory()
    path = directory / name
    if not path.is_file():
        raise DataNotFoundError(f"load_data: no data file {name!r} in {directory}")
    return path.read_bytes()
