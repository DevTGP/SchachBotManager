"""Builds the C# reference bot Material once for the cross test (E198)."""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2] / "bots" / "Material"


@pytest.fixture(scope="session")
def csharp_material(tmp_path_factory) -> list[str]:
    """Command that starts the C# bot; the shared core must be built under build/core."""
    dotnet = shutil.which("dotnet")
    assert dotnet, "the cross test needs the .NET SDK (dotnet) in PATH"
    output = tmp_path_factory.mktemp("material")
    subprocess.run(
        [dotnet, "build", str(PROJECT), "-c", "Release", "-o", str(output), "--nologo"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return [dotnet, str(output / "Material.dll")]
