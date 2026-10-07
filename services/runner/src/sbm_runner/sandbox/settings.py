"""Where the runner finds nsjail and its configuration; read from the environment (E86)."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

NSJAIL = "nsjail"
NONE = "none"
MODES = (NSJAIL, NONE)


@dataclass(frozen=True)
class SandboxSettings:
    """mode none runs only the reference bots, as plain processes; the image sets nsjail."""

    mode: str = NONE
    nsjail: Path = Path("/usr/local/bin/nsjail")
    config_dir: Path = Path("/opt/sbm/sandbox")
    # Mounted as /bot for the reference bots, which have no files of their own.
    no_files: Path = Path("/opt/sbm/no-files")

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "SandboxSettings":
        mode = env.get("SBM_SANDBOX") or NONE
        if mode not in MODES:
            raise ValueError(f"SBM_SANDBOX must be one of {', '.join(MODES)}, not {mode!r}")
        return cls(mode=mode)
