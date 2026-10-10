"""The one viewer window of a bot program: fed with the games and log lines of the bot (E106).

open_window starts the viewer once per program. Games pick it up through active_window, the log
writes into it as well. At the end of the program the SDK keeps the window open and waits until
the user closes it; ending the process (e.g. in the IDE) closes it too.
"""

import atexit
import contextlib
import os
import subprocess
import threading

from sbm import log as log_module
from sbm.log import Log
from sbm.records import GameInfo
from sbm.viewer import messages
from sbm.viewer.process import encode, program_path, start_process

# Set to a non-empty value, it keeps the window shut whatever the code asks for; the sandbox on
# the server sets it (E108).
DISABLE_VARIABLE = "SBM_NO_VIEWER"


class ViewerWindow:
    """Writes the viewer messages; after a broken pipe it stays silent."""

    def __init__(self, process: subprocess.Popen) -> None:
        self._process = process
        # Reentrant: a warning written while sending reaches send again through the log.
        self._lock = threading.RLock()
        self._sending = False
        self._open = True
        self._bot_white = True

    def is_open(self) -> bool:
        return self._open and self._process.poll() is None

    def game_started(self, bot: str, info: GameInfo) -> None:
        self._bot_white = info.color == 0
        self._send(messages.start(bot, info))

    def move_played(
        self,
        ply: int,
        uci: str,
        fen: str,
        by_bot: bool,
        clocks: tuple[int, int] | None = None,
        elapsed_ms: int | None = None,
        info: dict | None = None,
    ) -> None:
        """clocks: remaining times of the bot and of its opponent after the move."""
        if clocks is not None and not self._bot_white:
            clocks = (clocks[1], clocks[0])
        self._send(messages.move(ply, uci, fen, by_bot, clocks, elapsed_ms, info))

    def game_over(self, game_over: dict) -> None:
        """The referee's game_over; its final move goes ahead as a move of the opponent."""
        last_move, fen, ply = (game_over.get(key) for key in ("last_move", "fen", "ply"))
        if isinstance(last_move, str) and isinstance(fen, str) and isinstance(ply, int) and ply > 0:
            self.move_played(ply, last_move, fen, by_bot=False)
        self._send(game_over)

    def log_line(self, level: int, time: str, text: str) -> None:
        self._send(messages.log(level, time, text))

    def wait_until_closed(self) -> None:
        """Holds the program until the user closes the window; Ctrl+C stops waiting."""
        if self.is_open():
            Log.info("viewer: the program ends when the viewer window is closed")
            with contextlib.suppress(KeyboardInterrupt):
                self._process.wait()
        self.close()

    def close(self) -> None:
        with self._lock:
            self._open = False
            with contextlib.suppress(OSError):
                self._process.stdin.close()

    def _send(self, message: dict) -> None:
        with self._lock:
            if not self._open or self._sending:
                return
            self._sending = True
            try:
                self._process.stdin.write(encode(message))
                self._process.stdin.flush()
            except (OSError, ValueError):
                # The user closed the window, or it never opened (no display).
                self._open = False
            finally:
                self._sending = False


class _State:
    window: ViewerWindow | None = None
    missing_reported = False


def active_window() -> ViewerWindow | None:
    """The open viewer window of this program, if there is one."""
    window = _State.window
    return window if window is not None and window.is_open() else None


def open_window() -> ViewerWindow | None:
    """Opens the viewer window of this program, or returns the open one.

    None if SBM_NO_VIEWER is set, the package carries no viewer or it cannot start; the bot then
    runs without a window.
    """
    if (window := active_window()) is not None:
        return window
    if os.environ.get(DISABLE_VARIABLE):
        return None
    path = program_path()
    if not path.is_file():
        if not _State.missing_reported:
            _State.missing_reported = True
            Log.warn(f"viewer: {path.name} is not part of this installation; no window opens")
        return None
    try:
        process = start_process(path)
    except OSError as error:
        Log.warn(f"viewer: cannot start {path.name}: {error}")
        return None
    window = ViewerWindow(process)
    _State.window = window
    log_module.set_listener(window.log_line)
    atexit.register(window.wait_until_closed)
    return window
