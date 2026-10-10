"""The viewer program shipped in the package (sbm/bin), started as a process of its own (E106).

It reads one JSON message per line from stdin and ends when stdin ends. The window therefore
stays open as long as the bot program holds the pipe, and closes when the program is gone.
"""

import json
import subprocess
import sys
from pathlib import Path

PROGRAM = "sbm-viewer.exe" if sys.platform == "win32" else "sbm-viewer"

# Windows: leave the job object of the arena, so that freezing the bot does not freeze the
# window. Without the permission of the job, CreateProcess refuses and the viewer starts inside.
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


def program_path() -> Path:
    return Path(__file__).resolve().parent.parent / "bin" / PROGRAM


def _start(path: Path, **options: object) -> subprocess.Popen:
    return subprocess.Popen(
        [str(path)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, **options
    )


def start_process(path: Path) -> subprocess.Popen:
    """Starts the viewer; OSError if it cannot run."""
    if sys.platform != "win32":
        # A session of its own: the arena freezes the bot's process group (E67).
        return _start(path, start_new_session=True)
    try:
        return _start(path, creationflags=CREATE_BREAKAWAY_FROM_JOB)
    except PermissionError:
        return _start(path)


def encode(message: dict) -> bytes:
    return (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
