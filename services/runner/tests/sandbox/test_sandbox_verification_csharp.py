"""The verification of a C# bot in the real jail: sbm-build runs there (E203, E204)."""

import pytest
from sandbox_suite import BOTS, QUICK, RANDOM, REGULAR
from sbm.referee import Match
from sbm_store.verification_reports import ANALYSIS, BUILD, FAILED, PASSED

from sbm_runner.checkout import CHECKOUT_ROOT, write_program
from sbm_runner.verification.build_stage import BUILD_SECONDS, build_stages
from sbm_runner.verification.minimum_tests import TEST_GAMES, play_test

UPLOADED = "Uploaded.UploadedBot"


def build(sandbox, name: str, entry: str) -> tuple[list[dict], bytes | None]:
    completed = sandbox.build(BOTS / name, entry, BUILD_SECONDS)
    stages, ruleset, program = build_stages(completed, 0)
    assert ruleset is not None, completed.stderr.decode(errors="replace")
    return stages, program


@pytest.fixture
def uploaded(sandbox):
    """The clean bot's program, written where the runner writes the programs of its games."""
    stages, program = build(sandbox, "csharp_uploaded", UPLOADED)
    assert [(stage["stage"], stage["status"]) for stage in stages] == [
        (ANALYSIS, PASSED),
        (BUILD, PASSED),
    ], stages
    program_dir = write_program(CHECKOUT_ROOT, program)
    yield lambda: sandbox.program_player("Uploaded", BOTS / "csharp_uploaded", program_dir.path)
    program_dir.remove()


def test_the_analysis_finds_a_forbidden_type(sandbox):
    stages, program = build(sandbox, "csharp_forbidden", "Forbidden.ForbiddenBot")
    assert program is None
    [stage] = stages
    assert (stage["stage"], stage["status"]) == (ANALYSIS, FAILED)
    assert [(finding["file"], finding["line"]) for finding in stage["findings"]] == [
        ("ForbiddenBot.cs", 10)
    ]


def test_a_compiled_bot_reads_its_data(sandbox, uploaded):
    outcome = Match(uploaded(), sandbox.player(RANDOM), QUICK).play().outcome
    assert outcome.termination in REGULAR, outcome.detail


def test_a_compiled_bot_passes_the_minimum_tests(sandbox, uploaded):
    for game in TEST_GAMES:
        result = play_test(game, uploaded(), sandbox.player(RANDOM))
        assert result["passed"], result
