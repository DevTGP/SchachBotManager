"""The directory a jailed bot sees as /bot; for an uploaded bot a fresh copy of its files (E94).

The files come from GridFS and are checked again against the upload rules and the stored
hashes before they are written, so a damaged or altered entry never reaches the jail. A C# bot
also gets its compiled program in a directory of its own, mounted as /program (E204).
"""

import contextlib
import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pymongo.database import Database
from sbm.analysis.upload import UploadError, file_kind
from sbm_store import bot_files

CHECKOUT_ROOT = Path("/tmp/sbm-bots")
# The bot runs under an id of its own: everything must be readable by others, nothing writable.
_DIR_MODE = 0o755
_FILE_MODE = 0o644


class CheckoutError(Exception):
    """The stored files of a bot do not match its document; an infrastructure error."""


@dataclass(frozen=True)
class BotDir:
    """remove deletes the directory only if it is a checkout of its own, and the program's."""

    path: Path
    temporary: bool = False
    # The directory with the program of a C# bot.
    program: "BotDir | None" = None

    def remove(self) -> None:
        try:
            if self.temporary:
                shutil.rmtree(self.path, ignore_errors=True)
        finally:
            if self.program is not None:
                self.program.remove()


def checkout(db: Database, bot: dict, root: Path = CHECKOUT_ROOT) -> BotDir:
    bot_dir = _new_dir(root, "bot-")
    try:
        for entry in bot["files"]:
            _write(bot_dir.path, entry, bot["language"], bot_files.read_file(db, entry))
        program = bot.get("program")
        if program is not None:
            content = bot_files.read_file(db, program)
            if not _matches(program, content):
                raise CheckoutError("the stored program does not match its hash")
            bot_dir = BotDir(bot_dir.path, temporary=True, program=write_program(root, content))
    except BaseException:
        bot_dir.remove()
        raise
    return bot_dir


def write_program(root: Path, content: bytes) -> BotDir:
    """A new directory in root with content as the program of a C# bot; the caller removes it."""
    program_dir = _new_dir(root, "program-")
    try:
        target = program_dir.path / bot_files.PROGRAM
        target.write_bytes(content)
        target.chmod(_FILE_MODE)
    except BaseException:
        program_dir.remove()
        raise
    return program_dir


def _new_dir(root: Path, prefix: str) -> BotDir:
    root.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
    new_dir = BotDir(Path(tempfile.mkdtemp(prefix=prefix, dir=root)), temporary=True)
    try:
        new_dir.path.chmod(_DIR_MODE)
    except BaseException:
        new_dir.remove()
        raise
    return new_dir


def _write(root: Path, entry: dict, language: str, content: bytes) -> None:
    path = entry["path"]
    try:
        kind = file_kind(path, language)
    except UploadError as error:
        raise CheckoutError(f"stored path {path!r}: {error}") from None
    if kind != entry["kind"]:
        raise CheckoutError(f"stored file {path!r} is {entry['kind']}, its path says {kind}")
    if not _matches(entry, content):
        raise CheckoutError(f"stored file {path!r} does not match its hash")
    target = root.joinpath(*path.split("/"))
    for parent in reversed(target.relative_to(root).parents[:-1]):
        with contextlib.suppress(FileExistsError):
            (root / parent).mkdir(mode=_DIR_MODE)
        (root / parent).chmod(_DIR_MODE)
    # x: a second entry with the same path is an error, not an overwrite.
    with target.open("xb") as file:
        file.write(content)
    target.chmod(_FILE_MODE)


def _matches(entry: dict, content: bytes) -> bool:
    return len(content) == entry["size"] and hashlib.sha256(content).hexdigest() == entry["sha256"]
