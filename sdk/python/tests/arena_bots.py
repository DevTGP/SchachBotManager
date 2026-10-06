"""Small bots as source files for tests that start real processes."""

from pathlib import Path

FIRST_MOVE = """
import sbm

class First(sbm.Bot):
    def choose_move(self, board, clock):
        sbm.Log.info("thinking")
        return board.legal_moves()[0]

sbm.run(First)
"""

# Reports the longest pause its background thread has seen; frozen bots see long pauses.
GAP_REPORTER = """
import threading, time
import sbm

longest = 0.0

def tick():
    global longest
    last = time.monotonic()
    while True:
        time.sleep(0.01)
        now = time.monotonic()
        longest = max(longest, now - last)
        last = now

threading.Thread(target=tick, daemon=True).start()

class Gaps(sbm.Bot):
    def choose_move(self, board, clock):
        self.report(sbm.Info(text=f"{longest:.3f}"))
        return board.legal_moves()[0]

sbm.run(Gaps)
"""

SLOW = """
import time
import sbm

class Slow(sbm.Bot):
    def choose_move(self, board, clock):
        time.sleep(0.3)
        return board.legal_moves()[0]

sbm.run(Slow)
"""

CRASH_AFTER_READY = """
import sys
import sbm

class Crash(sbm.Bot):
    def choose_move(self, board, clock):
        sys.exit(3)

sbm.run(Crash)
"""


def write_bot(directory: Path, name: str, source: str) -> Path:
    path = directory / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    return path
