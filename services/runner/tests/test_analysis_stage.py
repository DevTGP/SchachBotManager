"""The analyzer's output is untrusted: only a well-formed report with the right exit code counts."""

import json

import pytest
from sbm_store.verification_reports import ANALYSIS, FAILED, PASSED
from uploads import CLEAN, DIRTY, FINDING

from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.analysis_stage import MAX_OUTPUT_BYTES, analysis_stage


def stage_of(returncode: int | None, report: object) -> tuple[dict, str | None]:
    stdout = report if isinstance(report, bytes) else json.dumps(report).encode()
    return analysis_stage(Completed(returncode, stdout, b""), 1234)


def test_a_clean_report_passes():
    stage, ruleset = stage_of(0, CLEAN)

    assert stage == {
        "stage": ANALYSIS,
        "status": PASSED,
        "duration_ms": 1234,
        "findings": [],
        "truncated": False,
        "problem": None,
    }
    assert ruleset == "python-test"


def test_findings_fail_and_are_kept():
    stage, ruleset = stage_of(1, DIRTY)

    assert (stage["status"], stage["problem"]) == (FAILED, "1 problem found")
    assert stage["findings"] == [FINDING]
    assert ruleset == "python-test"


def test_a_truncated_list_says_so():
    report = {**DIRTY, "findings": [FINDING, FINDING], "truncated": True}

    stage, _ = stage_of(1, report)

    assert stage["problem"] == "2 or more problems found"
    assert stage["truncated"]


def test_a_timeout_fails():
    stage, ruleset = analysis_stage(Completed(None, b"", b""), 60_000)

    assert stage["problem"] == "the analysis took longer than 60 s"
    assert ruleset is None


def test_too_much_output_fails():
    stage, _ = stage_of(0, b" " * (MAX_OUTPUT_BYTES + 1))

    assert "more than" in stage["problem"]


@pytest.mark.parametrize(
    ("returncode", "report"),
    [
        (2, CLEAN),
        (1, CLEAN),
        (0, DIRTY),
        (-9, b""),
        (0, b"not json"),
        (0, [CLEAN]),
        (0, {**CLEAN, "extra": 1}),
        (0, {**CLEAN, "ok": "yes"}),
        (1, {**DIRTY, "ok": True}),
        (1, {**DIRTY, "findings": [{**FINDING, "line": "1"}]}),
        (1, {**DIRTY, "findings": [{**FINDING, "line": True}]}),
        (1, {**DIRTY, "findings": [{**FINDING, "secret": "x"}]}),
        (1, {**DIRTY, "findings": ["bot.py:1"]}),
    ],
)
def test_anything_else_is_a_failed_analysis(returncode, report):
    stage, ruleset = stage_of(returncode, report)

    assert stage["status"] == FAILED
    assert stage["problem"] == f"the analysis failed with exit code {returncode}"
    assert (stage["findings"], ruleset) == ([], None)
