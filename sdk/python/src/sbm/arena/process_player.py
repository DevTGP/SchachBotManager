"""A bot as a local process: lines over stdin/stdout, its log from stderr on the console."""

import contextlib
import subprocess
import sys
import threading
from collections.abc import Callable
from typing import TextIO

from sbm.arena.process_group import POPEN_OPTIONS, ProcessGroup
from sbm.arena.stream_player import StreamPlayer
from sbm.referee import PlayerClosed

# Time a bot gets to end on its own after game_over, and to report its exit code.
GRACE_SECONDS = 2.0
EXIT_WAIT_SECONDS = 0.5

_print_lock = threading.Lock()


def warn_on_stderr(message: str) -> None:
    with _print_lock:
        print(f"warning: {message}", file=sys.stderr, flush=True)


class ProcessPlayer(StreamPlayer):
    """command is an argument list, or on Windows also a command line string.

    log receives the bot's stderr with the name in front of each line; None discards it.
    Freezing outside the own turn is best effort: if it fails, warn is called once and the bot
    keeps running unfrozen.
    """

    def __init__(
        self,
        name: str,
        command: list[str] | str,
        *,
        log: TextIO | None = sys.stderr,
        warn: Callable[[str], None] = warn_on_stderr,
    ) -> None:
        super().__init__(name)
        self._command = command
        self._log = log
        self._warn = warn
        self._process: subprocess.Popen | None = None
        self._group: ProcessGroup | None = None
        self._freezing = True
        self._log_thread: threading.Thread | None = None

    def start(self) -> None:
        try:
            self._process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL if self._log is None else subprocess.PIPE,
                **POPEN_OPTIONS,
            )
        except OSError as error:
            raise PlayerClosed(f"cannot start {self._command!r}: {error}") from None
        try:
            self._group = ProcessGroup(self._process.pid)
        except OSError as error:
            self._warn(f"{self.name} runs unfrozen and may leave processes behind: {error}")
        self._attach(self._process.stdout, self._process.stdin)
        if self._log is not None:
            self._log_thread = threading.Thread(
                target=self._forward_log, name=f"log {self.name}", daemon=True
            )
            self._log_thread.start()

    def _forward_log(self) -> None:
        with contextlib.suppress(OSError, ValueError):
            for raw in self._process.stderr:
                text = raw.decode("utf-8", "replace").rstrip("\r\n")
                with _print_lock:
                    print(f"[{self.name}] {text}", file=self._log, flush=True)

    def _closed(self) -> PlayerClosed:
        try:
            code = self._process.wait(EXIT_WAIT_SECONDS)
        except subprocess.TimeoutExpired:
            return super()._closed()
        return PlayerClosed(f"the bot exited with code {code}")

    def suspend(self) -> None:
        self._group_call("suspend", "freeze")

    def resume(self) -> None:
        self._group_call("resume", "resume")

    def _group_call(self, action: str, verb: str) -> None:
        if self._group is None or not self._freezing:
            return
        try:
            getattr(self._group, action)()
        except OSError as error:
            self._warn(f"cannot {verb} {self.name}, it runs unfrozen from now on: {error}")
            self._freezing = False
            with contextlib.suppress(OSError):
                self._group.resume()

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        self.resume()
        with contextlib.suppress(OSError, ValueError):
            process.stdin.close()
        if self.finished:
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(GRACE_SECONDS)
        # Also processes the bot started and left behind.
        self._kill()
        process.wait()
        if self._log_thread is not None:
            self._log_thread.join(EXIT_WAIT_SECONDS)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                with contextlib.suppress(OSError, ValueError):
                    stream.close()

    def _kill(self) -> None:
        if self._group is not None:
            try:
                self._group.kill()
            except OSError as error:
                self._warn(f"cannot end all processes of {self.name}: {error}")
            finally:
                self._group.close()
        if self._process.poll() is None:
            self._process.kill()
