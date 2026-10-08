"""A jailed command that runs to its end, such as the self-check or the static analysis."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from sbm_runner.sandbox.cgroup import BotCgroup


@dataclass(frozen=True)
class Completed:
    """returncode is None if the command ran out of time and was killed."""

    returncode: int | None
    stdout: bytes
    stderr: bytes


def run_once(command: list[str], *, cgroup: BotCgroup, bot_dir: Path, timeout: float) -> Completed:
    """Runs command in cgroup with bot_dir as /bot; the caller removes the cgroup."""
    process = subprocess.Popen(
        cgroup.enter(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"SBM_BOT_DIR": str(bot_dir)},
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
