"""The negative suite needs nsjail and a writable cgroup v2 tree, as in the runner container.

run-in-docker.sh starts it with the runner's rights; elsewhere it is skipped, and with
SBM_REQUIRE_SANDBOX=1 it fails instead.
"""

import os

import pytest
from sandbox_suite import BOTS, QUICK, RANDOM
from sbm.referee import Match, MatchSettings, Outcome, Player

from sbm_runner.sandbox.cgroup_tree import CGROUP_ROOT
from sbm_runner.sandbox.jail import Sandbox
from sbm_runner.sandbox.settings import NSJAIL, SandboxSettings


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """On GitHub every error becomes an annotation, which anyone can read, unlike the job's log."""
    if report.failed and os.environ.get("GITHUB_ACTIONS") == "true":
        title = _escape(f"{report.nodeid} ({report.when})", ":,")
        print(f"\n::error title={title}::{_escape(report.longreprtext[-4000:], '')}", flush=True)


def _escape(text: str, extra: str) -> str:
    """Escapes for a workflow command; titles also escape : and ,."""
    text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    for char in extra:
        text = text.replace(char, f"%{ord(char):02X}")
    return text


@pytest.fixture(scope="session")
def sandbox() -> Sandbox:
    settings = SandboxSettings.from_env(os.environ)
    if settings.mode != NSJAIL:
        if os.environ.get("SBM_REQUIRE_SANDBOX") == "1":
            pytest.fail("SBM_REQUIRE_SANDBOX=1, but SBM_SANDBOX is not nsjail")
        pytest.skip("needs the runner container (run-in-docker.sh)")
    sandbox = Sandbox(settings)
    sandbox.prepare()
    return sandbox


@pytest.fixture(autouse=True)
def no_leftovers(sandbox):
    """After every test all bot processes are gone and their cgroups removed."""
    yield
    assert [path.name for path in (CGROUP_ROOT / "bots").iterdir() if path.is_dir()] == []


@pytest.fixture
def jailed(sandbox):
    def jailed(name: str) -> Player:
        return sandbox.script_player(name, BOTS / name, "bot.py")

    return jailed


@pytest.fixture
def play(sandbox, jailed):
    """Plays the test bot as white against the jailed random bot."""

    def play(name: str, settings: MatchSettings = QUICK) -> Outcome:
        return Match(jailed(name), sandbox.player(RANDOM), settings).play().outcome

    return play
