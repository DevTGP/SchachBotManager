"""The C# template built against the NuGet package and played in the arena (E199, E201).

The package comes from SBM_NUGET_SOURCE (nuget.yml) or is packed from the repository. The
template is built outside the repository, as a user builds it, with its own package folder so
that no package of the same version from an earlier run is used.
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from sbm.arena.entrants import ProcessEntrant
from sbm.arena.series import Game, Series
from sbm.referee import MatchRecord, MatchSettings

TEMPLATE = Path(__file__).resolve().parents[4] / "templates" / "csharp"
ENDINGS = {
    "checkmate",
    "stalemate",
    "insufficient_material",
    "fifty_move_rule",
    "threefold_repetition",
    "max_moves",
}
SETTINGS = MatchSettings(initial_time_ms=120_000, max_moves=100, game_id="template")


def runtime_identifier() -> str:
    system = {"Linux": "linux", "Windows": "win", "Darwin": "osx"}[platform.system()]
    machine = platform.machine().lower()
    return f"{system}-{'arm64' if machine in ('arm64', 'aarch64') else 'x64'}"


def native_library() -> str:
    return {"Linux": "libsbm.so", "Windows": "sbm.dll", "Darwin": "libsbm.dylib"}[platform.system()]


def viewer_program() -> str:
    return "sbm-viewer.exe" if platform.system() == "Windows" else "sbm-viewer"


def template_version() -> str:
    project = (TEMPLATE / "MyBot.csproj").read_text()
    return re.search(r'Include="SchachBotManager" Version="([^"]+)"', project).group(1)


def test_template_pins_the_core_version(core_version):
    assert template_version() == core_version


def test_package_carries_the_core_for_this_platform(nuget_feed, core_version):
    package = nuget_feed / f"SchachBotManager.{core_version}.nupkg"
    names = zipfile.ZipFile(package).namelist()
    assert "lib/net10.0/SchachBotManager.dll" in names
    assert f"runtimes/{runtime_identifier()}/native/{native_library()}" in names


def test_package_carries_the_viewer_for_this_platform(nuget_feed, core_version):
    """The package built in nuget.yml carries the viewer (E206); the one packed here does not."""
    package = nuget_feed / f"SchachBotManager.{core_version}.nupkg"
    names = zipfile.ZipFile(package).namelist()
    viewer = f"runtimes/{runtime_identifier()}/native/{viewer_program()}"
    if os.environ.get("SBM_REQUIRE_VIEWER") != "1" and viewer not in names:
        pytest.skip("the package carries no viewer; nuget.yml builds it")
    assert viewer in names


def test_template_plays_against_material(tmp_path, dotnet, nuget_feed, core_version):
    project = tmp_path / "MyBot"
    shutil.copytree(TEMPLATE, project, ignore=shutil.ignore_patterns("bin", "obj"))
    subprocess.run(
        [dotnet, "restore", "--source", str(nuget_feed), "--packages", str(tmp_path / "packages")],
        cwd=project,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        [dotnet, "build", "--no-restore", "-c", "Release", "-warnaserror", "--nologo"],
        cwd=project,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    output = project / "bin" / "Release" / "net10.0"
    # Where the SDK looks for the viewer when the build is not for one platform (E206).
    viewer = output / "runtimes" / runtime_identifier() / "native" / viewer_program()
    if os.environ.get("SBM_REQUIRE_VIEWER") == "1":
        assert viewer.is_file(), viewer
    command = [dotnet, str(output / "MyBot.dll")]
    bot = ProcessEntrant("MyBot", command, sys.stderr)
    material = ProcessEntrant("Material", [sys.executable, "-m", "sbm.bots.material"], None)
    records: list[MatchRecord] = []

    def on_end(game: Game, record: MatchRecord) -> None:
        records.append(record)

    Series(bot, material, SETTINGS, 2).play(on_end=on_end)
    assert [record.white.lang for record in records] == ["csharp", "python"]
    for record in records:
        assert record.outcome.termination in ENDINGS, record.outcome
    white = records[0]
    assert white.white.sdk == core_version
    # The first move comes from data/book.txt, which the build copies next to the program.
    assert white.moves[0].info == {"text": "book"}
