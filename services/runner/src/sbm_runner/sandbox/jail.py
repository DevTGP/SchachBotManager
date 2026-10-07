"""The sandbox of the runner: prepares the cgroups, checks itself and jails every bot (E86)."""

import subprocess
from pathlib import Path

from sbm.referee import Player

from sbm_runner.players import UnsupportedBot, reference_module
from sbm_runner.sandbox.cgroup_tree import CgroupTree
from sbm_runner.sandbox.jail_player import JailPlayer
from sbm_runner.sandbox.settings import SandboxSettings

PYTHON = "/usr/local/bin/python3"
SELF_CHECK_SECONDS = 30
_SELF_CHECK_CODE = "import sbm.bots.material; print('jailed')"


class SandboxBroken(Exception):
    """The sandbox does not work; the runner does not start."""


class Sandbox:
    def __init__(self, settings: SandboxSettings, tree: CgroupTree | None = None) -> None:
        self._settings = settings
        self._tree = tree or CgroupTree()

    def prepare(self) -> None:
        """Run once before the first game."""
        try:
            self._tree.prepare()
        except OSError as error:
            raise SandboxBroken(f"cannot set up the cgroups: {error}") from error
        self._check()

    def player(self, bot: dict) -> Player:
        module = reference_module(bot)
        if module is None:
            raise UnsupportedBot(f"bot {bot['_id']} is uploaded; uploaded bots come with M3 step 3")
        return self._jailed(bot["name"], self._settings.no_files, ["-m", f"sbm.bots.{module}"])

    def script_player(self, name: str, bot_dir: Path, script: str) -> Player:
        """A Python bot whose files are in bot_dir, started with the file script there."""
        return self._jailed(name, bot_dir, [f"/bot/{script}"])

    def _jailed(self, name: str, bot_dir: Path, arguments: list[str]) -> JailPlayer:
        return JailPlayer(
            name,
            self._command([PYTHON, *arguments]),
            env={"SBM_BOT_DIR": str(bot_dir)},
            new_cgroup=self._tree.create,
        )

    def _command(self, argv: list[str]) -> list[str]:
        config = self._settings.config_dir / "python.cfg"
        return [str(self._settings.nsjail), "--config", str(config), "--", *argv]

    def _check(self) -> None:
        """Runs a reference bot's imports in the jail, as every game will."""
        try:
            cgroup = self._tree.create()
        except OSError as error:
            raise SandboxBroken(f"cannot create a bot's cgroup: {error}") from error
        try:
            result = subprocess.run(
                cgroup.enter(self._command([PYTHON, "-c", _SELF_CHECK_CODE])),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                env={"SBM_BOT_DIR": str(self._settings.no_files)},
                timeout=SELF_CHECK_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SandboxBroken(f"the self-check failed: {error}") from error
        finally:
            cgroup.kill()
            cgroup.remove()
        if result.returncode != 0 or result.stdout.strip() != b"jailed":
            stderr = result.stderr.decode("utf-8", "replace").strip()
            raise SandboxBroken(f"the self-check exited with {result.returncode}: {stderr}")
