"""Outside its turn a bot is frozen: not even its own threads get processor time (E26)."""

import time

import pytest
from sandbox_suite import QUICK
from sbm import WHITE
from sbm.referee.referee_messages import init

from sbm_runner.sandbox.cgroup_tree import CGROUP_ROOT


def cpu_usec(cgroup) -> int:
    lines = (cgroup / "cpu.stat").read_text().splitlines()
    return int(dict(line.split() for line in lines)["usage_usec"])


def wait_frozen(cgroup) -> None:
    deadline = time.monotonic() + 5
    while "frozen 1" not in (cgroup / "cgroup.events").read_text():
        assert time.monotonic() < deadline, "the cgroup did not freeze"
        time.sleep(0.01)


def state(cgroup) -> str:
    """What the cgroup holds, for a failure message: pids.current counts threads as well."""
    events = (cgroup / "cgroup.events").read_text().split()
    procs = (cgroup / "cgroup.procs").read_text().split()
    children = sorted(path.name for path in cgroup.iterdir() if path.is_dir())
    tasks = (cgroup / "pids.current").read_text().strip()
    return f"events {events}, processes {procs}, tasks {tasks}, children {children}"


def wait_for_cpu(cgroup, usec: int, problem: str) -> None:
    """The spinner runs as soon as it gets a processor; a busy CI machine may take a moment."""
    deadline = time.monotonic() + 5
    while (used := cpu_usec(cgroup)) <= usec:
        if time.monotonic() > deadline:
            pytest.fail(f"{problem}: {used} µs in all; {state(cgroup)}")
        time.sleep(0.05)


def test_frozen_bot_gets_no_processor_time(jailed):
    player = jailed("spinner")
    try:
        player.start()
        player.send(init(QUICK, WHITE, "nobody"))
        player.receive(time.monotonic_ns() + 10_000_000_000)
        (cgroup,) = (path for path in (CGROUP_ROOT / "bots").iterdir() if path.is_dir())
        wait_for_cpu(cgroup, cpu_usec(cgroup) + 100_000, "the spinner got no processor time")

        player.suspend()
        wait_frozen(cgroup)
        frozen = cpu_usec(cgroup)
        time.sleep(0.5)
        assert cpu_usec(cgroup) == frozen

        player.resume()
        wait_for_cpu(cgroup, frozen + 100_000, "the thawed spinner got no processor time")
    finally:
        player.close()
