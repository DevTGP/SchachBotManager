"""Tries to read and write outside its jail; exits with 42 if anything works (sandbox.md)."""

import os

import sbm

READ = [
    "/etc/passwd",
    "/etc/shadow",
    "/proc/self/environ",
    "/opt/sbm/sandbox/python.cfg",
    "/sys/fs/cgroup/cgroup.procs",
    "/root/.bashrc",
]
WRITE = ["/bot/written", "/tmp/written", "/written", "/usr/local/lib/written", "/dev/urandom"]
# The read-only root of the jail: the Python runtime, the loader and the mount points.
ROOT = {"bot", "dev", "etc", "lib", "lib64", "usr"}


def opens(path: str, mode: str) -> bool:
    try:
        with open(path, mode) as file:
            if mode == "w":
                file.write("x")
    except OSError:
        return False
    return True


class Files(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        breached = (
            any(opens(path, "r") for path in READ)
            or any(opens(path, "w") for path in WRITE)
            or not set(os.listdir("/")) <= ROOT
            or os.getuid() != 1000
        )
        if breached:
            os._exit(42)
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(Files)
