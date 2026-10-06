"""The process group of a bot on Linux and macOS, frozen with SIGSTOP and SIGCONT.

The bot starts in its own session, so its process group holds everything it starts and Ctrl+C
in the terminal reaches the arena only; the arena then ends the bots itself.
"""

import contextlib
import os
import signal

POPEN_OPTIONS = {"start_new_session": True}


class ProcessGroup:
    def __init__(self, pid: int) -> None:
        self._pgid = pid

    def _signal(self, number: int) -> None:
        # The group is gone once its last process has ended.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(self._pgid, number)

    def suspend(self) -> None:
        self._signal(signal.SIGSTOP)

    def resume(self) -> None:
        self._signal(signal.SIGCONT)

    def kill(self) -> None:
        self._signal(signal.SIGKILL)

    def close(self) -> None:
        pass
