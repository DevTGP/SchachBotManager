"""Outside its turn a bot is frozen: not even its own threads get processor time (E26)."""

import time

from sandbox_suite import QUICK
from sbm import WHITE
from sbm.referee.referee_messages import init

from sbm_runner.sandbox.cgroup_tree import CGROUP_ROOT


def cpu_usec(cgroup) -> int:
    lines = (cgroup / "cpu.stat").read_text().splitlines()
    return dict(line.split() for line in lines)["usage_usec"]


def wait_frozen(cgroup) -> None:
    deadline = time.monotonic() + 5
    while "frozen 1" not in (cgroup / "cgroup.events").read_text():
        assert time.monotonic() < deadline, "the cgroup did not freeze"
        time.sleep(0.01)


def wait_running(cgroup, usec: int) -> None:
    """Thawed, the spinner gets processor time again; a busy CI machine may take a moment."""
    deadline = time.monotonic() + 5
    while int(cpu_usec(cgroup)) <= usec:
        assert time.monotonic() < deadline, "the thawed bot got no processor time"
        time.sleep(0.05)


def test_frozen_bot_gets_no_processor_time(jailed):
    player = jailed("spinner")
    try:
        player.start()
        player.send(init(QUICK, WHITE, "nobody"))
        player.receive(time.monotonic_ns() + 10_000_000_000)
        (cgroup,) = (path for path in (CGROUP_ROOT / "bots").iterdir() if path.is_dir())

        player.suspend()
        wait_frozen(cgroup)
        frozen = int(cpu_usec(cgroup))
        time.sleep(0.5)
        assert int(cpu_usec(cgroup)) == frozen

        player.resume()
        wait_running(cgroup, frozen + 100_000)
    finally:
        player.close()
