"""The cgroup v2 of one bot process: limits, freezing, killing and the OOM count.

Errors are OSError; the caller treats them as infrastructure errors.
"""

import contextlib
import time
from pathlib import Path

# How long the kernel gets to empty a killed cgroup before it counts as stuck.
KILL_WAIT_SECONDS = 5.0
_POLL_SECONDS = 0.01
_ENTER = 'echo $$ > "$0" && exec "$@"'


class BotCgroup:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def create(cls, path: Path, *, memory_bytes: int, pids: int) -> "BotCgroup":
        path.mkdir()
        cgroup = cls(path)
        try:
            cgroup._write("memory.max", str(memory_bytes))
            # Without swap accounting the file is missing, and there is no swap to limit.
            if (path / "memory.swap.max").exists():
                cgroup._write("memory.swap.max", "0")
            # The OOM killer ends the whole bot, nsjail included, so its output closes.
            cgroup._write("memory.oom.group", "1")
            cgroup._write("pids.max", str(pids))
        except OSError:
            cgroup.remove()
            raise
        return cgroup

    def enter(self, command: list[str]) -> list[str]:
        """command behind a shell that moves itself into the cgroup before it becomes command.

        So every process of the bot counts from its first instruction on.
        """
        return ["/bin/sh", "-c", _ENTER, str(self.path / "cgroup.procs"), *command]

    def freeze(self) -> None:
        self._write("cgroup.freeze", "1")

    def thaw(self) -> None:
        self._write("cgroup.freeze", "0")

    def kill(self) -> None:
        """Ends every process, also frozen ones, and waits until the cgroup is empty."""
        self._write("cgroup.kill", "1")
        deadline = time.monotonic() + KILL_WAIT_SECONDS
        while self.populated():
            if time.monotonic() > deadline:
                raise OSError(f"{self.path} still has processes after cgroup.kill")
            time.sleep(_POLL_SECONDS)

    def populated(self) -> bool:
        return self._events("cgroup.events").get("populated", 0) > 0

    def oom_killed(self) -> bool:
        return self._events("memory.events").get("oom_kill", 0) > 0

    def remove(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.path.rmdir()

    def _events(self, name: str) -> dict[str, int]:
        lines = (self.path / name).read_text().splitlines()
        return {key: int(value) for key, value in (line.split() for line in lines)}

    def _write(self, name: str, value: str) -> None:
        (self.path / name).write_text(value)
