"""The sandbox of the runner: prepares the cgroups, checks itself and jails every bot (E86).

Each language has a runtime of its own with its own nsjail configuration (runtimes.py); the
self-check starts every one of them once, as every game will.
"""

import dataclasses
import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from sbm.analysis.upload import CSHARP, PYTHON
from sbm.referee import Player

from sbm_runner.checkout import BotDir
from sbm_runner.players import UnsupportedBot, reference_module
from sbm_runner.sandbox.cgroup_tree import CgroupTree
from sbm_runner.sandbox.jail_player import JailPlayer
from sbm_runner.sandbox.run_once import Completed, run_once
from sbm_runner.sandbox.runtimes import RUNTIMES, Runtime
from sbm_runner.sandbox.settings import SandboxSettings

SELF_CHECK_SECONDS = 30


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
        # Versions of each language's runtime and its SDK, known after prepare.
        self.runtimes: dict[str, dict[str, str]] = {}

    def prepare(self) -> None:
        """Run once before the first game."""
        try:
            self._tree.prepare()
        except OSError as error:
            raise SandboxBroken(f"cannot set up the cgroups: {error}") from error
        self.runtimes = {language: self._check(runtime) for language, runtime in RUNTIMES.items()}

    def player(self, bot: dict) -> Player:
        module = reference_module(bot)
        if module is not None:
            return self._jailed(
                bot["name"], RUNTIMES[PYTHON], self._no_files, ["-m", f"sbm.bots.{module}"]
            )
        runtime = _runtime(bot["_id"], bot.get("language"))
        if self._files is None:
            raise UnsupportedBot(f"bot {bot['_id']} is uploaded, and this sandbox has no files")
        if runtime is RUNTIMES[CSHARP]:
            if bot.get("program") is None:
                raise UnsupportedBot(f"bot {bot['_id']} has no compiled program")
            return self._jailed(bot["name"], runtime, lambda: self.checkout(bot), [])
        return self._jailed(
            bot["name"], runtime, lambda: self.checkout(bot), [f"/bot/{bot['entry']}"]
        )

    def checkout(self, bot: dict) -> BotDir:
        """The files of an uploaded bot in a new directory; the caller removes it."""
        if self._files is None:
            raise UnsupportedBot(f"bot {bot['_id']} is uploaded, and this sandbox has no files")
        return self._files(bot)

    def candidate(self, bot: dict, bot_dir: Path, program_dir: Path | None) -> Player:
        """The bot under verification from its checked-out files and, for C#, its new program."""
        if _runtime(bot["_id"], bot.get("language")) is RUNTIMES[CSHARP]:
            if program_dir is None:
                raise ValueError(f"bot {bot['_id']} is written in C# and has no program")
            return self.program_player(bot["name"], bot_dir, program_dir)
        return self.script_player(bot["name"], bot_dir, bot["entry"], bot["language"])

    def script_player(self, name: str, bot_dir: Path, script: str, language: str) -> Player:
        """A Python or JavaScript bot whose files are in bot_dir, started with the file script."""
        runtime = _runtime(name, language)
        return self._jailed(name, runtime, lambda: BotDir(bot_dir), [f"/bot/{script}"])

    def program_player(self, name: str, bot_dir: Path, program_dir: Path) -> Player:
        """A C# bot whose files are in bot_dir and whose compiled program is in program_dir."""
        return self._jailed(
            name, RUNTIMES[CSHARP], lambda: BotDir(bot_dir, program=BotDir(program_dir)), []
        )

    def analyze(self, bot_dir: Path, entry: str, timeout: float, language: str) -> Completed:
        """sbm-check of the bot's runtime over bot_dir, in the jail: it reads untrusted files."""
        runtime = _runtime(bot_dir, language)
        return self._run(runtime, runtime.analysis(entry), BotDir(bot_dir), timeout)

    def build(self, bot_dir: Path, entry: str, timeout: float) -> Completed:
        """sbm-build over the C# sources in bot_dir, in the jail: Roslyn reads untrusted files.

        It analyzes and compiles in one process (E203); its own files and the reference
        assemblies are part of the runtime, nothing from /bot is loaded.
        """
        runtime = RUNTIMES[CSHARP]
        return self._run(
            runtime,
            [*runtime.build, "--entry", entry, *runtime.references, "/bot"],
            BotDir(bot_dir),
            timeout,
        )

    def _run(self, runtime: Runtime, argv: list[str], bot_dir: BotDir, timeout: float) -> Completed:
        cgroup = self._tree.create()
        try:
            return run_once(
                self._command(runtime, argv),
                cgroup=cgroup,
                bot_dir=self._mounted(bot_dir),
                timeout=timeout,
            )
        finally:
            cgroup.kill()
            cgroup.remove()

    def _no_files(self) -> BotDir:
        return BotDir(self._settings.no_files)

    def _mounted(self, bot_dir: BotDir) -> BotDir:
        """Without a program of its own, /program is the empty directory."""
        if bot_dir.program is not None:
            return bot_dir
        return dataclasses.replace(bot_dir, program=self._no_files())

    def _jailed(
        self,
        name: str,
        runtime: Runtime,
        bot_dir: Callable[[], BotDir],
        arguments: list[str],
    ) -> JailPlayer:
        return JailPlayer(
            name,
            self._command(runtime, [*runtime.start, *arguments]),
            bot_dir=lambda: self._mounted(bot_dir()),
            new_cgroup=self._tree.create,
        )

    def _command(self, runtime: Runtime, argv: list[str]) -> list[str]:
        config = self._settings.config_dir / runtime.config
        return [str(self._settings.nsjail), "--config", str(config), "--", *argv]

    def _check(self, runtime: Runtime) -> dict[str, str]:
        """Starts the runtime in the jail as a game would; returns the versions it reports."""
        try:
            cgroup = self._tree.create()
        except OSError as error:
            raise SandboxBroken(f"cannot create a bot's cgroup: {error}") from error
        try:
            result = run_once(
                self._command(runtime, list(runtime.self_check)),
                cgroup=cgroup,
                bot_dir=self._mounted(self._no_files()),
                timeout=SELF_CHECK_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise SandboxBroken(f"the self-check of {runtime.name} failed: {error}") from error
        finally:
            cgroup.kill()
            cgroup.remove()
        if result.returncode is None:
            raise SandboxBroken(
                f"the self-check of {runtime.name} took longer than {SELF_CHECK_SECONDS} s"
            )
        versions = _versions(result.stdout, runtime.name) if result.returncode == 0 else None
        if versions is None:
            stderr = result.stderr.decode("utf-8", "replace").strip()
            raise SandboxBroken(
                f"the self-check of {runtime.name} exited with {result.returncode}: {stderr}"
            )
        return versions


def _runtime(bot: object, language: str | None) -> Runtime:
    runtime = RUNTIMES.get(language) if language is not None else None
    if runtime is None:
        raise UnsupportedBot(f"bot {bot} is written in {language!r}")
    return runtime


def _versions(stdout: bytes, name: str) -> dict[str, str] | None:
    """{name: version of the runtime, "sdk": version of the SDK}, or None."""
    try:
        versions = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(versions, dict) or sorted(versions) != sorted([name, "sdk"]):
        return None
    if not all(isinstance(value, str) for value in versions.values()):
        return None
    return versions
