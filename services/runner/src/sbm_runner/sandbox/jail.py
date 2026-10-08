"""The sandbox of the runner: prepares the cgroups, checks itself and jails every bot (E86)."""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from sbm.referee import Player

from sbm_runner.checkout import BotDir
from sbm_runner.players import UnsupportedBot, reference_module
from sbm_runner.sandbox.cgroup_tree import CgroupTree
from sbm_runner.sandbox.jail_player import JailPlayer
from sbm_runner.sandbox.run_once import Completed, run_once
from sbm_runner.sandbox.settings import SandboxSettings

PYTHON = "/usr/local/bin/python3"
LANGUAGE = "python"
SELF_CHECK_SECONDS = 30
_SELF_CHECK_CODE = (
    "import json, sys, sbm, sbm.bots.material; "
    "print(json.dumps({'python': sys.version.split()[0], 'sdk': sbm.__version__}))"
)


class SandboxBroken(Exception):
    """The sandbox does not work; the runner does not start."""


class Sandbox:
    """files copies the files of an uploaded bot into a directory of its own (E94)."""

    def __init__(
        self,
        settings: SandboxSettings,
        tree: CgroupTree | None = None,
        *,
        files: Callable[[dict], BotDir] | None = None,
    ) -> None:
        self._settings = settings
        self._tree = tree or CgroupTree()
        self._files = files
        # Versions of Python and the SDK in the bots' runtime, known after prepare.
        self.runtime: dict[str, str] = {}

    def prepare(self) -> None:
        """Run once before the first game."""
        try:
            self._tree.prepare()
        except OSError as error:
            raise SandboxBroken(f"cannot set up the cgroups: {error}") from error
        self.runtime = self._check()

    def player(self, bot: dict) -> Player:
        module = reference_module(bot)
        if module is not None:
            return self._jailed(bot["name"], self._no_files, ["-m", f"sbm.bots.{module}"])
        if bot.get("language") != LANGUAGE:
            raise UnsupportedBot(f"bot {bot['_id']} is written in {bot.get('language')!r}")
        if self._files is None:
            raise UnsupportedBot(f"bot {bot['_id']} is uploaded, and this sandbox has no files")
        return self._jailed(bot["name"], lambda: self.checkout(bot), [f"/bot/{bot['entry']}"])

    def checkout(self, bot: dict) -> BotDir:
        """The files of an uploaded bot in a new directory; the caller removes it."""
        if self._files is None:
            raise UnsupportedBot(f"bot {bot['_id']} is uploaded, and this sandbox has no files")
        return self._files(bot)

    def script_player(self, name: str, bot_dir: Path, script: str) -> Player:
        """A Python bot whose files are in bot_dir, started with the file script there."""
        return self._jailed(name, lambda: BotDir(bot_dir), [f"/bot/{script}"])

    def analyze(self, bot_dir: Path, entry: str, timeout: float) -> Completed:
        """sbm-check of the runtime over bot_dir, in the jail: the analysis reads untrusted files.

        -I keeps /bot off the module path, so no uploaded file can stand in for the analyzer.
        """
        command = [PYTHON, "-I", "-m", "sbm.analysis", "--json", "--entry", entry, "/bot"]
        cgroup = self._tree.create()
        try:
            return run_once(self._command(command), cgroup=cgroup, bot_dir=bot_dir, timeout=timeout)
        finally:
            cgroup.kill()
            cgroup.remove()

    def _no_files(self) -> BotDir:
        return BotDir(self._settings.no_files)

    def _jailed(self, name: str, bot_dir: Callable[[], BotDir], arguments: list[str]) -> JailPlayer:
        return JailPlayer(
            name,
            self._command([PYTHON, *arguments]),
            bot_dir=bot_dir,
            new_cgroup=self._tree.create,
        )

    def _command(self, argv: list[str]) -> list[str]:
        config = self._settings.config_dir / "python.cfg"
        return [str(self._settings.nsjail), "--config", str(config), "--", *argv]

    def _check(self) -> dict[str, str]:
        """Runs a reference bot's imports in the jail, as every game will; returns the versions."""
        try:
            cgroup = self._tree.create()
        except OSError as error:
            raise SandboxBroken(f"cannot create a bot's cgroup: {error}") from error
        try:
            result = run_once(
                self._command([PYTHON, "-c", _SELF_CHECK_CODE]),
                cgroup=cgroup,
                bot_dir=self._settings.no_files,
                timeout=SELF_CHECK_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise SandboxBroken(f"the self-check failed: {error}") from error
        finally:
            cgroup.kill()
            cgroup.remove()
        if result.returncode is None:
            raise SandboxBroken(f"the self-check took longer than {SELF_CHECK_SECONDS} s")
        runtime = _versions(result.stdout) if result.returncode == 0 else None
        if runtime is None:
            stderr = result.stderr.decode("utf-8", "replace").strip()
            raise SandboxBroken(f"the self-check exited with {result.returncode}: {stderr}")
        return runtime


def _versions(stdout: bytes) -> dict[str, str] | None:
    try:
        versions = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(versions, dict) or sorted(versions) != ["python", "sdk"]:
        return None
    if not all(isinstance(value, str) for value in versions.values()):
        return None
    return versions
