"""The viewer program shipped in the package: reads a game and ends with its input (E106).

Runs without a display through SDL's offscreen driver. Skipped if the package carries no viewer
(built with SBM_VIEWER=OFF); the wheel tests require it with SBM_REQUIRE_VIEWER=1.
"""

import os
import subprocess

import pytest
from protocol_schemas import VIEWER, example
from test_viewer_messages import INFO

from sbm.viewer import messages
from sbm.viewer.process import encode, program_path


@pytest.fixture
def program():
    path = program_path()
    if not path.is_file():
        if os.environ.get("SBM_REQUIRE_VIEWER") == "1":
            pytest.fail(f"{path} is missing")
        pytest.skip("this installation carries no viewer")
    return path


def test_shows_a_game_and_ends_with_its_input(program, tmp_path):
    screenshot = tmp_path / "viewer.bmp"
    lines = [
        messages.start("Material", INFO),
        example("move.own", VIEWER),
        example("move.opponent", VIEWER),
        example("log.info", VIEWER),
        example("game_over.checkmate", VIEWER),
    ]
    result = subprocess.run(
        [str(program), "--screenshot", str(screenshot)],
        input=b"".join(encode(line) for line in lines),
        capture_output=True,
        timeout=60,
        env={**os.environ, "SDL_VIDEO_DRIVER": "offscreen"},
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert screenshot.read_bytes()[:2] == b"BM"
