"""The verification in the real jail: the analyzer runs there, and an uploaded bot passes (E92)."""

import pytest
from sandbox_suite import ENTRIES, LANGUAGES, RANDOM, REGULAR, bot_dir
from sbm_store.verification_reports import FAILED, PASSED

from sbm_runner.verification.analysis_stage import ANALYSIS_SECONDS, analysis_stage
from sbm_runner.verification.minimum_tests import TEST_GAMES, play_test


def analyze(sandbox, name: str, language: str) -> dict:
    entry = ENTRIES[language]
    completed = sandbox.analyze(bot_dir(name, language), entry, ANALYSIS_SECONDS, language)
    stage, ruleset = analysis_stage(completed, 0)
    assert ruleset is not None, completed.stderr.decode(errors="replace")
    return stage


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_analysis_passes_a_clean_bot(sandbox, language):
    stage = analyze(sandbox, "uploaded", language)
    assert (stage["status"], stage["findings"]) == (PASSED, [])


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_analysis_finds_a_forbidden_import(sandbox, language):
    stage = analyze(sandbox, "forbidden", language)
    assert stage["status"] == FAILED
    findings = [(finding["file"], finding["line"]) for finding in stage["findings"]]
    assert findings == [(ENTRIES[language], 3)]


@pytest.mark.parametrize("language", LANGUAGES)
def test_an_uploaded_bot_reads_its_module_and_data(play, language):
    outcome = play("uploaded", language=language)
    assert outcome.termination in REGULAR, outcome.detail


@pytest.mark.parametrize("language", LANGUAGES)
def test_an_uploaded_bot_passes_the_minimum_tests(sandbox, jailed, language):
    for game in TEST_GAMES:
        result = play_test(game, jailed("uploaded", language), sandbox.player(RANDOM))
        assert result["passed"], result
