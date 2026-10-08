"""Choosing the sandbox and starting it, without nsjail; the jail itself is tested in sandbox/."""

import pytest
from bson import ObjectId
from sbm_store.bots import BUILTIN_PREFIX

from sbm_runner.checkout import BotDir
from sbm_runner.cli import start_sandbox
from sbm_runner.players import UnsupportedBot, plain_player
from sbm_runner.sandbox.jail import Sandbox, SandboxBroken, _versions
from sbm_runner.sandbox.settings import NONE, NSJAIL, SandboxSettings

UPLOADED = {
    "_id": ObjectId(),
    "name": "Uploaded",
    "language": "python",
    "entry": "bot.py",
    "source_ref": "gridfs",
}
UNKNOWN = {"_id": ObjectId(), "name": "Unknown", "source_ref": BUILTIN_PREFIX + "sbm_runner"}


def test_without_a_setting_there_is_no_sandbox():
    assert SandboxSettings.from_env({}).mode == NONE
    assert SandboxSettings.from_env({"SBM_SANDBOX": ""}).mode == NONE
    assert SandboxSettings.from_env({"SBM_SANDBOX": "nsjail"}).mode == NSJAIL


def test_an_unknown_sandbox_is_an_error():
    with pytest.raises(ValueError, match="SBM_SANDBOX"):
        SandboxSettings.from_env({"SBM_SANDBOX": "docker"})


def test_without_sandbox_only_reference_bots_play():
    assert start_sandbox(SandboxSettings(), db=None) is None
    with pytest.raises(UnsupportedBot, match="needs the sandbox"):
        plain_player(UPLOADED)
    with pytest.raises(UnsupportedBot, match="unknown reference bot"):
        plain_player(UNKNOWN)


class BrokenTree:
    def prepare(self) -> None:
        raise PermissionError(30, "Read-only file system")


def test_a_cgroup_tree_that_cannot_be_set_up_stops_the_runner():
    sandbox = Sandbox(SandboxSettings(mode=NSJAIL), tree=BrokenTree())
    with pytest.raises(SandboxBroken, match="cannot set up the cgroups"):
        sandbox.prepare()


def test_uploaded_bots_need_their_files():
    sandbox = Sandbox(SandboxSettings(mode=NSJAIL), tree=BrokenTree())
    with pytest.raises(UnsupportedBot, match="has no files"):
        sandbox.player(UPLOADED)
    with pytest.raises(UnsupportedBot, match="has no files"):
        sandbox.checkout(UPLOADED)
    with pytest.raises(UnsupportedBot, match="unknown reference bot"):
        sandbox.player(UNKNOWN)


def test_only_python_bots_run():
    sandbox = Sandbox(SandboxSettings(mode=NSJAIL), tree=BrokenTree(), files=BotDir)
    with pytest.raises(UnsupportedBot, match="'java'"):
        sandbox.player({**UPLOADED, "language": "java"})


def test_the_self_check_reports_both_versions():
    assert _versions(b'{"python": "3.12.1", "sdk": "0.4.0"}\n') == {
        "python": "3.12.1",
        "sdk": "0.4.0",
    }
    assert _versions(b"3.12.1") is None
    assert _versions(b'{"python": "3.12.1"}') is None
    assert _versions(b'{"python": "3.12.1", "sdk": 4}') is None
