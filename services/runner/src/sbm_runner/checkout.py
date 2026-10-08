"""The directory a jailed bot sees as /bot; for an uploaded bot a fresh copy of its files (E94).

The files come from GridFS and are checked again against the upload rules and the stored
hashes before they are written, so a damaged or altered entry never reaches the jail.
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
    """remove deletes the directory only if it is a checkout of its own."""

    path: Path
    temporary: bool = False

    def remove(self) -> None:
        if self.temporary:
            shutil.rmtree(self.path, ignore_errors=True)


def checkout(db: Database, bot: dict, root: Path = CHECKOUT_ROOT) -> BotDir:
    root.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
    bot_dir = BotDir(Path(tempfile.mkdtemp(prefix="bot-", dir=root)), temporary=True)
    try:
        bot_dir.path.chmod(_DIR_MODE)
        for entry in bot["files"]:
            _write(bot_dir.path, entry, bot_files.read_file(db, entry))
    except BaseException:
        bot_dir.remove()
        raise
    return bot_dir


def _write(root: Path, entry: dict, content: bytes) -> None:
    path = entry["path"]
    try:
        kind = file_kind(path)
    except UploadError as error:
        raise CheckoutError(f"stored path {path!r}: {error}") from None
    if kind != entry["kind"]:
        raise CheckoutError(f"stored file {path!r} is {entry['kind']}, its path says {kind}")
    if len(content) != entry["size"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
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
