"""The process group of a bot on Linux and macOS."""

import os
import subprocess
import sys

import pytest

if sys.platform == "win32":
    pytest.skip("POSIX process groups only", allow_module_level=True)

from sbm.arena.posix_group import POPEN_OPTIONS, ProcessGroup


def test_signals_to_an_exited_group_are_ignored():
    process = subprocess.Popen([sys.executable, "-c", "pass"], **POPEN_OPTIONS)
    group = ProcessGroup(process.pid)
    # Exited but not reaped yet, as a bot right after game_over: macOS answers EPERM here.
    os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOWAIT)
    group.suspend()
    group.resume()
    group.kill()
    assert process.wait(10) == 0
    # Reaped: the group no longer exists.
    group.resume()
    group.kill()
