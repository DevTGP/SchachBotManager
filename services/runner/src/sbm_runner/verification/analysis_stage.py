"""The static analysis of an uploaded bot as a stage of its report (statische-analyse.md, E90).

The analyzer runs in the jail; whatever it prints is checked before it lands in the report.
A crash, a timeout or output that is no report rejects the bot.
"""

import json

from sbm_store.verification_reports import ANALYSIS, FAILED, PASSED

from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.findings import is_section, problems_found

ANALYSIS_SECONDS = 60
MAX_OUTPUT_BYTES = 1024 * 1024


def analysis_stage(completed: Completed, duration_ms: int) -> tuple[dict, str | None]:
    """The stage for the report and the ruleset the analyzer used, if it reported one."""
    report = None
    if completed.returncode is None:
        problem = f"the analysis took longer than {ANALYSIS_SECONDS} s"
    elif len(completed.stdout) > MAX_OUTPUT_BYTES:
        problem = f"the analysis wrote more than {MAX_OUTPUT_BYTES} bytes"
    else:
        report = _report(completed.stdout)
        if report is None or completed.returncode != (0 if report["ok"] else 1):
            report = None
            problem = f"the analysis failed with exit code {completed.returncode}"
        elif not report["ok"]:
            problem = problems_found(report)
        else:
            problem = None
    stage = {
        "stage": ANALYSIS,
        "status": PASSED if problem is None else FAILED,
        "duration_ms": duration_ms,
        "findings": report["findings"] if report else [],
        "truncated": report["truncated"] if report else False,
        "problem": problem,
    }
    return stage, report["ruleset"] if report else None


def _report(stdout: bytes) -> dict | None:
    try:
        report = json.loads(stdout)
    except ValueError:
        return None
    if not is_section(report, extra=("ruleset",)) or not isinstance(report["ruleset"], str):
        return None
    return report
