"""Uploaded bots for the tests, and a Verifier that runs them without nsjail."""

import base64
import json
import sys
from pathlib import Path

from bson import ObjectId
from sbm.analysis.upload import CSHARP, DATA, JAVASCRIPT, PYTHON, SOURCE
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
# A JavaScript bot; FakeVerifier lets the random bot play for it.
JAVASCRIPT_FILES = [
    ("bot.js", SOURCE, b'import * as sbm from "schachbotmanager";\n'),
    ("data/book.txt", DATA, b"e2e4\n"),
]
# Exits before it says hello.
CRASHING = [("bot.py", SOURCE, b"raise SystemExit(3)\n")]
CLEAN = {"ruleset": "python-test", "ok": True, "truncated": False, "findings": []}
FINDING = {"rule": "import", "file": "bot.py", "line": 1, "message": "socket is not allowed"}
DIRTY = {**CLEAN, "ok": False, "findings": [FINDING]}

# A C# bot for the fake build: its "program" is the Python bot of GOOD in one file, which the
# fake candidate runs from the program directory.
CSHARP_FILES = [
    ("MyBot.cs", SOURCE, b"class First : Sbm.Bot {}\n"),
    ("data/book.txt", DATA, b"e2e4\n"),
]
CSHARP_ENTRY = "MyBot.First"
PROGRAM = (
    b"import sbm\n\n\n"
    b"class First(sbm.Bot):\n"
    b"    def choose_move(self, board, clock):\n"
    b"        return board.legal_moves()[0]\n\n\n"
    b"sbm.run(First)\n"
)
SECTION = {"ok": True, "truncated": False, "findings": []}
BUILT = {
    "ruleset": "csharp-test",
    "analysis": SECTION,
    "build": SECTION,
    "program": base64.b64encode(PROGRAM).decode(),
}
CS_FINDING = {"rule": "CS0103", "file": "MyBot.cs", "line": 1, "message": "x does not exist"}
NOT_BUILT = {**BUILT, "build": {**SECTION, "ok": False, "findings": [CS_FINDING]}, "program": None}


def upload_csharp(db, files=CSHARP_FILES, **kwargs) -> dict:
    return upload(db, files, language=CSHARP, entry=CSHARP_ENTRY, **kwargs)


def upload(
    db,
    files=GOOD,
    *,
    name: str = "Uploaded",
    version: str = "1.0.0",
    language: str = PYTHON,
    entry: str = "bot.py",
) -> dict:
    """Stores an uploaded bot and queues its verification, as the web API will."""
    bot_id = ObjectId()
    now = utc_now()
    entries = bot_files.store_files(db, bot_id, files)
    bot = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=name,
        version=version,
        language=language,
        entry=entry,
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
    """The bot's files are checked out for real; analysis and build say what report is given."""

    def __init__(self, db, root: Path, report: dict = CLEAN, built: dict = BUILT) -> None:
        self.runtimes = {
            PYTHON: {"python": "3.12.1", "sdk": "0.4.0"},
            JAVASCRIPT: {"node": "24.1.0", "sdk": "0.4.0"},
            CSHARP: {"dotnet": "10.0.13", "sdk": "0.4.0"},
        }
        self.report = report
        self.built = built
        self.programs: list[Path] = []
        self.error: BaseException | None = None
        self.checked_out: list[BotDir] = []
        self.analyzed: list[str] = []
        self.languages: list[str] = []
        self._db = db
        self._root = root

    def checkout(self, bot: dict) -> BotDir:
        bot_dir = checkout(self._db, bot, self._root)
        self.checked_out.append(bot_dir)
        return bot_dir

    def analyze(self, bot_dir: Path, entry: str, timeout: float, language: str) -> Completed:
        if self.error is not None:
            raise self.error
        self.languages.append(language)
        self.analyzed = sorted(
            path.relative_to(bot_dir).as_posix() for path in bot_dir.rglob("*") if path.is_file()
        )
        stdout = json.dumps(self.report).encode()
        return Completed(0 if self.report["ok"] else 1, stdout, b"")

    def build(self, bot_dir: Path, entry: str, timeout: float) -> Completed:
        if self.error is not None:
            raise self.error
        self.analyzed = sorted(
            path.relative_to(bot_dir).as_posix() for path in bot_dir.rglob("*") if path.is_file()
        )
        stdout = json.dumps(self.built).encode()
        return Completed(1 if self.built["program"] is None else 0, stdout, b"")

    def candidate(self, bot: dict, bot_dir: Path, program_dir: Path | None) -> Player:
        self.languages.append(bot["language"])
        if bot["language"] == JAVASCRIPT:
            return CheckedPlayer(
                bot["name"], [sys.executable, "-m", "sbm.bots.random_mover"], log=None
            )
        if program_dir is None:
            script = bot_dir / bot["entry"]
        else:
            self.programs.append(program_dir)
            script = program_dir / bot_files.PROGRAM
        return CheckedPlayer(bot["name"], [sys.executable, str(script)], log=None)

    def player(self, bot: dict) -> Player:
        return plain_player(bot)
