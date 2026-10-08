"""The verification in the real jail: the analyzer runs there, and an uploaded bot passes (E92)."""

from sandbox_suite import BOTS, RANDOM, REGULAR
from sbm_store.verification_reports import FAILED, PASSED

from sbm_runner.verification.analysis_stage import ANALYSIS_SECONDS, analysis_stage
from sbm_runner.verification.minimum_tests import TEST_GAMES, play_test


def analyze(sandbox, name: str) -> dict:
    completed = sandbox.analyze(BOTS / name, "bot.py", ANALYSIS_SECONDS)
    stage, ruleset = analysis_stage(completed, 0)
    assert ruleset is not None, completed.stderr.decode(errors="replace")
    return stage


def test_the_analysis_passes_a_clean_bot(sandbox):
    stage = analyze(sandbox, "uploaded")
    assert (stage["status"], stage["findings"]) == (PASSED, [])


def test_the_analysis_finds_a_forbidden_import(sandbox):
    stage = analyze(sandbox, "forbidden")
    assert stage["status"] == FAILED
    assert [(finding["file"], finding["line"]) for finding in stage["findings"]] == [("bot.py", 3)]


def test_an_uploaded_bot_reads_its_module_and_data(play):
    outcome = play("uploaded")
    assert outcome.termination in REGULAR, outcome.detail


def test_an_uploaded_bot_passes_the_minimum_tests(sandbox, jailed):
    for game in TEST_GAMES:
        result = play_test(game, jailed("uploaded"), sandbox.player(RANDOM))
        assert result["passed"], result
