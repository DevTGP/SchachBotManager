"""sbm-build's output is untrusted: only a consistent report with the right exit code counts."""

import json

import pytest
from sbm_store.verification_reports import ANALYSIS, BUILD, FAILED, PASSED
from uploads import BUILT, CS_FINDING, NOT_BUILT, PROGRAM, SECTION

from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.build_stage import MAX_OUTPUT_BYTES, build_stages

NOT_ANALYZED = {
    **BUILT,
    "analysis": {**SECTION, "ok": False, "findings": [CS_FINDING]},
    "build": None,
    "program": None,
}


def stages_of(returncode: int | None, report: object):
    stdout = report if isinstance(report, bytes) else json.dumps(report).encode()
    return build_stages(Completed(returncode, stdout, b""), 1234)


def test_a_compiled_bot_passes_both_stages_with_its_program():
    stages, ruleset, program = stages_of(0, BUILT)

    assert [(stage["stage"], stage["status"]) for stage in stages] == [
        (ANALYSIS, PASSED),
        (BUILD, PASSED),
    ]
    # The run is one process: its time counts for the last stage it reached.
    assert [stage["duration_ms"] for stage in stages] == [0, 1234]
    assert (ruleset, program) == ("csharp-test", PROGRAM)


def test_errors_of_the_compiler_fail_the_build():
    stages, ruleset, program = stages_of(1, NOT_BUILT)

    assert stages[0]["status"] == PASSED
    assert (stages[1]["status"], stages[1]["problem"]) == (FAILED, "1 problem found")
    assert stages[1]["findings"] == [CS_FINDING]
    assert (ruleset, program) == ("csharp-test", None)


def test_findings_of_the_analysis_stop_before_the_build():
    stages, ruleset, program = stages_of(1, NOT_ANALYZED)

    assert [stage["stage"] for stage in stages] == [ANALYSIS]
    assert (stages[0]["status"], stages[0]["duration_ms"]) == (FAILED, 1234)
    assert stages[0]["findings"] == [CS_FINDING]
    assert (ruleset, program) == ("csharp-test", None)


def test_a_timeout_fails_the_build():
    stages, ruleset, program = build_stages(Completed(None, b"", b""), 120_000)

    assert [stage["stage"] for stage in stages] == [BUILD]
    assert stages[0]["problem"] == "the build took longer than 120 s"
    assert (ruleset, program) == (None, None)


def test_too_much_output_fails_the_build():
    stages, _, program = stages_of(0, b" " * (MAX_OUTPUT_BYTES + 1))

    assert "more than" in stages[0]["problem"]
    assert program is None


@pytest.mark.parametrize(
    ("returncode", "report"),
    [
        (1, BUILT),
        (0, NOT_BUILT),
        (0, NOT_ANALYZED),
        (2, NOT_BUILT),
        (-31, b""),
        (0, b"not json"),
        (0, [BUILT]),
        (0, {**BUILT, "extra": 1}),
        (0, {**BUILT, "ruleset": None}),
        (0, {**BUILT, "build": None}),
        (0, {**BUILT, "program": None}),
        (0, {**BUILT, "program": ""}),
        (0, {**BUILT, "program": "not base64!"}),
        (0, {**BUILT, "program": 5}),
        (1, {**NOT_BUILT, "program": BUILT["program"]}),
        (1, {**NOT_BUILT, "program": 0}),
        (1, {**NOT_ANALYZED, "build": SECTION}),
        (0, {**BUILT, "analysis": {**SECTION, "ok": False}}),
        (1, {**NOT_BUILT, "build": {**SECTION, "findings": [{**CS_FINDING, "line": "1"}]}}),
    ],
)
def test_anything_else_is_a_failed_build(returncode, report):
    stages, ruleset, program = stages_of(returncode, report)

    assert [(stage["stage"], stage["status"]) for stage in stages] == [(BUILD, FAILED)]
    assert stages[0]["problem"] == f"the build failed with exit code {returncode}"
    assert (stages[0]["findings"], ruleset, program) == ([], None, None)
