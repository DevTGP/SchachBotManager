"""The cgroup files of one bot, on a plain directory standing in for cgroupfs."""

import pytest

from sbm_runner.sandbox import cgroup as cgroup_module
from sbm_runner.sandbox.cgroup import BotCgroup


@pytest.fixture
def bot(tmp_path) -> BotCgroup:
    return BotCgroup.create(tmp_path / "bot-1", memory_bytes=1024, pids=8)


def read(cgroup: BotCgroup, name: str) -> str:
    return (cgroup.path / name).read_text()


def test_create_sets_the_limits(bot):
    assert read(bot, "memory.max") == "1024"
    assert read(bot, "memory.oom.group") == "1"
    assert read(bot, "pids.max") == "8"
    # Without swap accounting the kernel has no memory.swap.max; nothing is written then.
    assert not (bot.path / "memory.swap.max").exists()


def test_two_bots_never_share_a_cgroup(bot):
    with pytest.raises(FileExistsError):
        BotCgroup.create(bot.path, memory_bytes=1, pids=1)


def test_enter_moves_the_shell_into_the_cgroup_before_the_command(bot):
    command = bot.enter(["nsjail", "--", "python3"])
    assert command[:2] == ["/bin/sh", "-c"]
    assert command[3] == str(bot.path / "cgroup.procs")
    assert command[4:] == ["nsjail", "--", "python3"]


def test_freeze_and_thaw(bot):
    bot.freeze()
    assert read(bot, "cgroup.freeze") == "1"
    bot.thaw()
    assert read(bot, "cgroup.freeze") == "0"


def test_oom_kill_is_read_from_memory_events(bot):
    (bot.path / "memory.events").write_text("low 0\nhigh 0\nmax 3\noom 1\noom_kill 0\n")
    assert not bot.oom_killed()
    (bot.path / "memory.events").write_text("low 0\nhigh 0\nmax 9\noom 2\noom_kill 1\n")
    assert bot.oom_killed()


def test_kill_waits_until_the_cgroup_is_empty(bot):
    (bot.path / "cgroup.events").write_text("populated 0\nfrozen 0\n")
    bot.kill()
    assert read(bot, "cgroup.kill") == "1"


def test_a_cgroup_that_stays_populated_is_an_error(bot, monkeypatch):
    monkeypatch.setattr(cgroup_module, "KILL_WAIT_SECONDS", 0.05)
    (bot.path / "cgroup.events").write_text("populated 1\nfrozen 1\n")
    with pytest.raises(OSError, match="still has processes"):
        bot.kill()


def test_removing_a_removed_cgroup_is_fine(tmp_path):
    BotCgroup(tmp_path / "gone").remove()
