"""The uploaded files of bots in the GridFS bucket bot_files (E82, E94).

Each file is stored on its own with bot_id and path as metadata; the bot document lists them
with size and SHA-256, and source_hash covers the whole upload. A C# bot also has its program,
compiled once by the verification (E204), stored the same way under the name PROGRAM.
"""

import contextlib
import hashlib
from collections.abc import Iterable

from bson import ObjectId
from gridfs import GridFSBucket
from gridfs.errors import NoFile
from pymongo.database import Database

from sbm_store.names import BOT_FILES

# The name of a compiled program in the bucket and in the jail (/program/bot.dll).
PROGRAM = "bot.dll"


def bucket(db: Database) -> GridFSBucket:
    return GridFSBucket(db, bucket_name=BOT_FILES)


def store_files(
    db: Database, bot_id: ObjectId, files: Iterable[tuple[str, str, bytes]]
) -> list[dict]:
    """Stores (path, kind, content) for a bot that is yet to be inserted; returns its entries.

    Paths and kinds come checked from the upload rules of the SDK.
    """
    files_bucket = bucket(db)
    entries = []
    for path, kind, content in files:
        file_id = files_bucket.upload_from_stream(
            path, content, metadata={"bot_id": bot_id, "path": path}
        )
        entries.append(
            {
                "path": path,
                "kind": kind,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "file_id": file_id,
            }
        )
    return entries


def store_program(db: Database, bot_id: ObjectId, content: bytes) -> dict:
    """Stores the compiled program of a bot; returns the entry for its program field."""
    file_id = bucket(db).upload_from_stream(
        PROGRAM, content, metadata={"bot_id": bot_id, "program": True}
    )
    return {"size": len(content), "sha256": hashlib.sha256(content).hexdigest(), "file_id": file_id}


def delete_files(db: Database, entries: Iterable[dict]) -> None:
    """Removes stored files or a program, for an upload that could not be inserted or a bot
    that is deleted."""
    files_bucket = bucket(db)
    for entry in entries:
        with contextlib.suppress(NoFile):
            files_bucket.delete(entry["file_id"])


def read_file(db: Database, entry: dict) -> bytes:
    return bucket(db).open_download_stream(entry["file_id"]).read()


def source_hash(entries: Iterable[dict]) -> str:
    """SHA-256 over the sorted lines path NUL sha256 LF, the same for the same files."""
    lines = sorted(f"{entry['path']}\0{entry['sha256']}\n" for entry in entries)
    return hashlib.sha256("".join(lines).encode()).hexdigest()
