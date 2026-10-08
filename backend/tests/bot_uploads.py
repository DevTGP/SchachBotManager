"""Multipart bodies for POST /bots, and uploaded bots written through the store."""

import io

from bson import ObjectId
from sbm_store import bot_files, bots, verification_reports

from accounts import CSRF
from stored_games import NOW

BOT = b"import sbm\n\n\nclass Bot(sbm.Bot):\n    pass\n"
FILES = {"bot.py": BOT, "helper.py": b"X = 1\n", "data/book.txt": b"e2e4\n"}


def upload_form(
    files: dict[str, bytes] = FILES,
    *,
    name: str = "Sharp",
    version: str = "1.0.0",
    **fields,
) -> dict:
    return {
        "name": name,
        "version": version,
        "language": "python",
        **fields,
        "paths": list(files),
        # The file name of each part does not count; paths do.
        "files": [(io.BytesIO(content), "blob") for content in files.values()],
    }


def post_upload(client, files: dict[str, bytes] = FILES, **fields):
    return client.post(
        "/api/v1/bots",
        data=upload_form(files, **fields),
        content_type="multipart/form-data",
        headers=CSRF,
    )


def store_bot(
    db,
    owner_id,
    *,
    name: str = "Sharp",
    version: str = "1.0.0",
    now=NOW,
    files: tuple[tuple[str, str, bytes], ...] = (("bot.py", "source", BOT),),
) -> dict:
    """An uploaded bot written through the store, as POST /bots leaves it."""
    bot_id = ObjectId()
    entries = bot_files.store_files(db, bot_id, files)
    bot = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=name,
        version=version,
        language="python",
        entry="bot.py",
        files=entries,
        source_hash=bot_files.source_hash(entries),
        owner_id=owner_id,
        previous=bots.latest(db, name),
        now=now,
    )
    assert bots.insert(db, bot)
    return bot


def verify(db, bot: dict, *, passed: bool = True) -> dict:
    """Ends the verification as the runner does, with a report of one analysis stage."""
    finding = {"rule": "import", "file": "bot.py", "line": 1, "message": "socket is not allowed"}
    stage = {
        "stage": "analysis",
        "status": "passed" if passed else "failed",
        "duration_ms": 120,
        "findings": [] if passed else [finding],
        "truncated": False,
        "problem": None if passed else "1 finding",
    }
    report = verification_reports.new_report(
        bot_id=bot["_id"],
        job_id=ObjectId(),
        started_at=NOW,
        finished_at=NOW,
        passed=passed,
        ruleset="python-1",
        runtime={"python": "3.12.1", "sdk": "0.4.0"},
        stages=[stage],
    )
    verification_reports.insert(db, report)
    assert bots.finish_verification(
        db,
        bot["_id"],
        verified=passed,
        report_id=report["_id"],
        rejection=None if passed else {"stage": "analysis", "reason": "1 finding"},
        sdk_version="0.4.0",
        runtime_version="3.12.1",
        now=NOW,
    )
    return bots.get(db, bot["_id"])
