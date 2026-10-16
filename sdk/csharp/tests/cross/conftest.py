"""Builds the C# reference bot Material (E198) and the NuGet package (E199) once per run."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

CSHARP = Path(__file__).resolve().parents[2]
PROJECT = CSHARP / "bots" / "Material"
CORE = CSHARP.parent / "core" / "CMakeLists.txt"


@pytest.fixture(scope="session")
def core_version() -> str:
    """The version of the core, which is that of every SDK (E36)."""
    return re.search(r"project\(sbm_core VERSION ([0-9.]+)", CORE.read_text()).group(1)


@pytest.fixture(scope="session")
def dotnet() -> str:
    path = shutil.which("dotnet")
    assert path, "the cross test needs the .NET SDK (dotnet) in PATH"
    return path


@pytest.fixture(scope="session")
def csharp_material(tmp_path_factory, dotnet) -> list[str]:
    """Command that starts the C# bot; the shared core must be built under build/core."""
    output = tmp_path_factory.mktemp("material")
    subprocess.run(
        [dotnet, "build", str(PROJECT), "-c", "Release", "-o", str(output), "--nologo"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return [dotnet, str(output / "Material.dll")]


@pytest.fixture(scope="session")
def nuget_feed(tmp_path_factory, dotnet) -> Path:
    """Directory with the package: SBM_NUGET_SOURCE (nuget.yml), otherwise packed here."""
    configured = os.environ.get("SBM_NUGET_SOURCE")
    if configured:
        return Path(configured)
    feed = tmp_path_factory.mktemp("feed")
    subprocess.run(
        [dotnet, "pack", str(CSHARP / "src" / "Sbm"), "-c", "Release", "-o", str(feed)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return feed
