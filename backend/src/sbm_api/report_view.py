"""Verification reports as the API shows them (schema VerificationReport, E92).

Only the listed fields go out; ids of the bot and the job stay inside.
"""

from sbm_api.timestamps import timestamp

FINDING_FIELDS = ("rule", "file", "line", "message")
TEST_FIELDS = ("name", "color", "result", "termination", "detail", "plies", "passed", "problem")


def report_view(report: dict) -> dict:
    return {
        "result": report["result"],
        "ruleset": report["ruleset"],
        "runtime": report["runtime"],
        "started_at": timestamp(report["started_at"]),
        "finished_at": timestamp(report["finished_at"]),
        "stages": [_stage_view(stage) for stage in report["stages"]],
    }


def _stage_view(stage: dict) -> dict:
    view = {
        "stage": stage["stage"],
        "status": stage["status"],
        "duration_ms": stage["duration_ms"],
        "problem": stage["problem"],
    }
    if "findings" in stage:
        view["findings"] = [_pick(finding, FINDING_FIELDS) for finding in stage["findings"]]
        view["truncated"] = stage["truncated"]
    if "tests" in stage:
        view["tests"] = [_pick(test, TEST_FIELDS) for test in stage["tests"]]
    return view


def _pick(item: dict, fields: tuple[str, ...]) -> dict:
    return {field: item[field] for field in fields}
