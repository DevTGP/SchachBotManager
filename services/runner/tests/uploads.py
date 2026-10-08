"""Uploaded bots for the tests, and a Verifier that runs them without nsjail."""

import json
import sys
from pathlib import Path

from bson import ObjectId
from sbm.analysis.upload import DATA, SOURCE
from sbm.arena.process_player import ProcessPlayer
from sbm.referee import Player
from sbm_store import bot_files, bots, jobs

from sbm_runner.checkout import BotDir, checkout
from sbm_runner.players import plain_player
from sbm_runner.sandbox.run_once import Completed
from sbm_runner.worker import utc_now

# Plays the first legal move; the helper module shows that its own files import.
GOOD = [
    (
        "bot.py",
        SOURCE,
        b"import sbm\nfrom helper import first\n\n\n"
        b"class First(sbm.Bot):\n"
        b"    def choose_move(self, board, clock):\n"
        b"        return first(board.legal_moves())\n\n\n"
        b'if __name__ == "__main__":\n'
        b"    sbm.run(First)\n",
    ),
    ("helper.py", SOURCE, b"def first(moves):\n    return moves[0]\n"),
    ("data/book.txt", DATA, b"e2e4\n"),
]
# Exits before it says hello.
CRASHING = [("bot.py", SOURCE, b"raise SystemExit(3)\n")]
CLEAN = {"ruleset": "python-test", "ok": True, "truncated": False, "findings": []}
FINDING = {"rule": "import", "file": "bot.py", "line": 1, "message": "socket is not allowed"}
DIRTY = {**CLEAN, "ok": False, "findings": [FINDING]}


def upload(db, files=GOOD, *, name: str = "Uploaded", version: str = "1.0.0") -> dict:
    """Stores an uploaded bot and queues its verification, as the web API will."""
    bot_id = ObjectId()
    now = utc_now()
    entries = bot_files.store_files(db, bot_id, files)
    bot = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=name,
        version=version,
        language="python",
        entry="bot.py",
        files=entries,
        source_hash=bot_files.source_hash(entries),
        owner_id=ObjectId(),
        previous=bots.latest(db, name),
        now=now,
    )
    assert bots.insert(db, bot)
    jobs.insert(db, jobs.new_verification_job(bot_id, now=now))
    return bot


class CheckedPlayer(ProcessPlayer):
    """Tells after close how the bot ended, as JailPlayer does; here always cleanly."""

    exited_cleanly = True
    stderr_bytes = 0


class FakeVerifier:
    """The bot's files are checked out for real; the analysis says what report is given."""

    def __init__(self, db, root: Path, report: dict = CLEAN) -> None:
        self.runtime = {"python": "3.12.1", "sdk": "0.4.0"}
        self.report = report
        self.error: BaseException | None = None
        self.checked_out: list[BotDir] = []
        self.analyzed: list[str] = []
        self._db = db
        self._root = root

    def checkout(self, bot: dict) -> BotDir:
        bot_dir = checkout(self._db, bot, self._root)
        self.checked_out.append(bot_dir)
        return bot_dir

    def analyze(self, bot_dir: Path, entry: str, timeout: float) -> Completed:
        if self.error is not None:
            raise self.error
        self.analyzed = sorted(
            path.relative_to(bot_dir).as_posix() for path in bot_dir.rglob("*") if path.is_file()
        )
        stdout = json.dumps(self.report).encode()
        return Completed(0 if self.report["ok"] else 1, stdout, b"")

    def script_player(self, name: str, bot_dir: Path, script: str) -> Player:
        return CheckedPlayer(name, [sys.executable, str(bot_dir / script)], log=None)

    def player(self, bot: dict) -> Player:
        return plain_player(bot)
