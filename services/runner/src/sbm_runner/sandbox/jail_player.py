"""A bot in nsjail inside its own cgroup: lines over stdin/stdout, frozen outside its turn."""

import contextlib
import logging
import subprocess
from collections.abc import Callable

from sbm.arena.stream_player import StreamPlayer
from sbm.referee import PlayerClosed

from sbm_runner.checkout import BotDir
from sbm_runner.sandbox.cgroup import BotCgroup
from sbm_runner.sandbox.limits import MEMORY_LIMIT_MIB
from sbm_runner.sandbox.stderr_tail import StderrTail

log = logging.getLogger(__name__)

# Time a bot gets to end on its own after game_over, and to report its exit code.
GRACE_SECONDS = 2.0
EXIT_WAIT_SECONDS = 0.5


class JailPlayer(StreamPlayer):
    """command starts nsjail; nsjail reads SBM_BOT_DIR from its environment, the bot never.

    When it starts, bot_dir provides the directory mounted as /bot and new_cgroup the bot's
    cgroup; close removes both. Errors there are infrastructure errors, those of the cgroup are
    OSError. After close, exited_cleanly says whether the bot ended on its own with code 0 within
    the grace period after game_over, and stderr_bytes how much it wrote to stderr.
    """

    def __init__(
        self,
        name: str,
        command: list[str],
        *,
        bot_dir: Callable[[], BotDir],
        new_cgroup: Callable[[], BotCgroup],
    ) -> None:
        super().__init__(name)
        self._command = command
        self._new_bot_dir = bot_dir
        self._new_cgroup = new_cgroup
        self._bot_dir: BotDir | None = None
        self._cgroup: BotCgroup | None = None
        self._process: subprocess.Popen | None = None
        self._stderr: StderrTail | None = None
        self._failed = False
        self.exited_cleanly = False

    @property
    def stderr_bytes(self) -> int:
        return 0 if self._stderr is None else self._stderr.total

    def start(self) -> None:
        self._bot_dir = self._new_bot_dir()
        self._cgroup = self._new_cgroup()
        self._process = subprocess.Popen(
            self._cgroup.enter(self._command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"SBM_BOT_DIR": str(self._bot_dir.path)},
            close_fds=True,
        )
        self._stderr = StderrTail(self._process.stderr, self.name)
        self._attach(self._process.stdout, self._process.stdin)

    def send(self, message: dict) -> None:
        try:
            super().send(message)
        except PlayerClosed:
            raise self._closed() from None

    def _closed(self) -> PlayerClosed:
        self._failed = True
        with contextlib.suppress(subprocess.TimeoutExpired):
            self._process.wait(EXIT_WAIT_SECONDS)
        if self._cgroup.oom_killed():
            return PlayerClosed(
                f"the bot exceeded its memory limit of {MEMORY_LIMIT_MIB} MiB", "memory_limit"
            )
        code = self._process.poll()
        if code is None:
            return super()._closed()
        return PlayerClosed(f"the bot exited with code {code}")

    def suspend(self) -> None:
        if self._process is not None:
            self._cgroup.freeze()

    def resume(self) -> None:
        if self._process is not None:
            self._cgroup.thaw()

    def close(self) -> None:
        try:
            if self._process is not None:
                self._end(self._process)
        finally:
            try:
                if self._cgroup is not None:
                    self._cgroup.remove()
            finally:
                if self._bot_dir is not None:
                    self._bot_dir.remove()

    def _end(self, process: subprocess.Popen) -> None:
        try:
            self._cgroup.thaw()
            with contextlib.suppress(OSError, ValueError):
                process.stdin.close()
            if self.finished:
                with contextlib.suppress(subprocess.TimeoutExpired):
                    self.exited_cleanly = process.wait(GRACE_SECONDS) == 0
            # cgroup.kill also reaches processes the bot started, and frozen ones.
            self._cgroup.kill()
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            self._log_stderr()
            for stream in (process.stdout, process.stderr):
                with contextlib.suppress(OSError, ValueError):
                    stream.close()

    def _log_stderr(self) -> None:
        text = self._stderr.text(EXIT_WAIT_SECONDS).strip()
        if text:
            level = logging.INFO if self._failed else logging.DEBUG
            log.log(level, "stderr of %s (end):\n%s", self.name, text)
