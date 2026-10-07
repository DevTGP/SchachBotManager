"""The runner's cgroup v2 tree inside its container (sandbox.md, E86).

The container has its own cgroup namespace, so /sys/fs/cgroup is its own branch. A cgroup with
processes cannot pass controllers to its children, so the runner moves itself to runner/ and
puts every bot into a cgroup of its own below bots/.
"""

import contextlib
import ctypes
import os
import secrets
from pathlib import Path

from sbm_runner.sandbox.cgroup import BotCgroup
from sbm_runner.sandbox.limits import MEMORY_LIMIT_MIB, PIDS_LIMIT

CGROUP_ROOT = Path("/sys/fs/cgroup")
CONTROLLERS = ("memory", "pids")

# From <sys/mount.h>; the remount keeps the flags Docker set.
_MS_NOSUID = 2
_MS_NODEV = 4
_MS_NOEXEC = 8
_MS_REMOUNT = 32
_MS_RELATIME = 1 << 21


class CgroupTree:
    def __init__(self, root: Path = CGROUP_ROOT) -> None:
        self._root = root
        self._bots = root / "bots"

    def prepare(self) -> None:
        """Run once at startup, as root with CAP_SYS_ADMIN; also ends bots of an earlier run."""
        if not (self._root / "cgroup.controllers").exists():
            raise OSError(f"{self._root} is not a cgroup v2 tree; the sandbox needs cgroup v2")
        _remount_writable(self._root)
        available = (self._root / "cgroup.controllers").read_text().split()
        missing = [name for name in CONTROLLERS if name not in available]
        if missing:
            raise OSError(f"the container's cgroup lacks the controllers {missing}")
        leaf = self._root / "runner"
        leaf.mkdir(exist_ok=True)
        if not (leaf / "cgroup.kill").exists():
            raise OSError("cgroup.kill is missing; the sandbox needs Linux 5.14 or newer")
        for pid in (self._root / "cgroup.procs").read_text().split():
            # A process that ended meanwhile need not move.
            with contextlib.suppress(ProcessLookupError):
                (leaf / "cgroup.procs").write_text(pid)
        enable = " ".join(f"+{name}" for name in CONTROLLERS)
        (self._root / "cgroup.subtree_control").write_text(enable)
        self._bots.mkdir(exist_ok=True)
        (self._bots / "cgroup.subtree_control").write_text(enable)
        self._remove_leftovers()

    def create(self) -> BotCgroup:
        return BotCgroup.create(
            self._bots / f"bot-{secrets.token_hex(6)}",
            memory_bytes=MEMORY_LIMIT_MIB * 1024 * 1024,
            pids=PIDS_LIMIT,
        )

    def _remove_leftovers(self) -> None:
        for path in self._bots.iterdir():
            if path.is_dir():
                cgroup = BotCgroup(path)
                cgroup.kill()
                cgroup.remove()


def _remount_writable(path: Path) -> None:
    """Docker mounts the cgroup tree read-only unless the container is privileged."""
    if not os.statvfs(path).f_flag & os.ST_RDONLY:
        return
    libc = ctypes.CDLL(None, use_errno=True)
    flags = _MS_REMOUNT | _MS_NOSUID | _MS_NODEV | _MS_NOEXEC | _MS_RELATIME
    if libc.mount(None, os.fsencode(path), None, flags, None) != 0:
        error = ctypes.get_errno()
        raise OSError(error, f"cannot remount {path} writable: {os.strerror(error)}")
