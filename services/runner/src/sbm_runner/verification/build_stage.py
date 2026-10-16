"""Analysis and build of a C# bot as stages of its report (verifikation.md, E203).

sbm-build analyzes and compiles in one process in the jail and prints one report with both
sections and the program. Whatever it prints is checked before it lands in the report; a crash,
a timeout or output that is no report gives one failed build stage. The tool measures no time of
its own, so the whole run counts for the last stage it reached.
"""

import base64
import binascii
import json

from sbm_store.verification_reports import ANALYSIS, BUILD, FAILED, PASSED

from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.findings import is_section, problems_found

BUILD_SECONDS = 120
# The program in Base64 and up to a hundred findings in each section.
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_REPORT_KEYS = ["analysis", "build", "program", "ruleset"]


def build_stages(
    completed: Completed, duration_ms: int
) -> tuple[list[dict], str | None, bytes | None]:
    """The stages for the report, the ruleset of the analysis and the program, if it compiled."""
    if completed.returncode is None:
        return [_failed(f"the build took longer than {BUILD_SECONDS} s", duration_ms)], None, None
    if len(completed.stdout) > MAX_OUTPUT_BYTES:
        problem = f"the build wrote more than {MAX_OUTPUT_BYTES} bytes"
        return [_failed(problem, duration_ms)], None, None
    report = _report(completed.stdout)
    if report is None or completed.returncode != (1 if report["program"] is None else 0):
        problem = f"the build failed with exit code {completed.returncode}"
        return [_failed(problem, duration_ms)], None, None
    if report["build"] is None:
        return [_stage(ANALYSIS, report["analysis"], duration_ms)], report["ruleset"], None
    stages = [_stage(ANALYSIS, report["analysis"], 0), _stage(BUILD, report["build"], duration_ms)]
    return stages, report["ruleset"], report["program"]


def _stage(name: str, section: dict, duration_ms: int) -> dict:
    return {
        "stage": name,
        "status": PASSED if section["ok"] else FAILED,
        "duration_ms": duration_ms,
        "findings": section["findings"],
        "truncated": section["truncated"],
        "problem": None if section["ok"] else problems_found(section),
    }


def _failed(problem: str, duration_ms: int) -> dict:
    return {
        "stage": BUILD,
        "status": FAILED,
        "duration_ms": duration_ms,
        "findings": [],
        "truncated": False,
        "problem": problem,
    }


def _report(stdout: bytes) -> dict | None:
    """The report with the program decoded; None if it is no report or contradicts itself."""
    try:
        report = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(report, dict) or sorted(report) != _REPORT_KEYS:
        return None
    if not isinstance(report["ruleset"], str) or not is_section(report["analysis"]):
        return None
    analyzed = report["analysis"]["ok"]
    if analyzed != (report["build"] is not None):
        return None
    if report["build"] is not None and not is_section(report["build"]):
        return None
    compiled = analyzed and report["build"]["ok"]
    if not compiled:
        return report if report["program"] is None else None
    if not isinstance(report["program"], str):
        return None
    try:
        report["program"] = base64.b64decode(report["program"], validate=True)
    except (binascii.Error, ValueError):
        return None
    return report if report["program"] else None
