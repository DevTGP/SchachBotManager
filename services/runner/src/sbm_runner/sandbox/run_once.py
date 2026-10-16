"""A jailed command that runs to its end, such as the self-check or the static analysis."""

import subprocess
from dataclasses import dataclass

from sbm_runner.checkout import BotDir
from sbm_runner.sandbox.cgroup import BotCgroup


@dataclass(frozen=True)
class Completed:
    """returncode is None if the command ran out of time and was killed."""

    returncode: int | None
    stdout: bytes
    stderr: bytes


def jail_env(bot_dir: BotDir) -> dict[str, str]:
    """The environment of nsjail: what it mounts as /bot and /program; the bot never sees it.

    The sandbox gives every directory a program directory, an empty one if there is no program.
    """
    if bot_dir.program is None:
        raise ValueError(f"{bot_dir.path} has no program directory")
    return {"SBM_BOT_DIR": str(bot_dir.path), "SBM_PROGRAM_DIR": str(bot_dir.program.path)}


def run_once(
    command: list[str], *, cgroup: BotCgroup, bot_dir: BotDir, timeout: float
) -> Completed:
    """Runs command in cgroup with bot_dir mounted; the caller removes the cgroup."""
    process = subprocess.Popen(
        cgroup.enter(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=jail_env(bot_dir),
        close_fds=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return Completed(process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        # cgroup.kill also ends what nsjail started, so the pipes close.
        cgroup.kill()
        stdout, stderr = process.communicate()
        return Completed(None, stdout, stderr)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
