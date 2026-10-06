"""A single finding reported by one of the checks."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Problem:
    path: Path
    message: str
