"""The findings of the analyzers as they print them, checked before they land in a report."""

_SECTION_KEYS = ["findings", "ok", "truncated"]
_FINDING_KEYS = ["file", "line", "message", "rule"]


def is_section(section: object, *, extra: tuple[str, ...] = ()) -> bool:
    """{"ok", "truncated", "findings"} and the keys extra, which the caller checks."""
    return (
        isinstance(section, dict)
        and sorted(section) == sorted([*_SECTION_KEYS, *extra])
        and isinstance(section["ok"], bool)
        and isinstance(section["truncated"], bool)
        and isinstance(section["findings"], list)
        and all(_is_finding(finding) for finding in section["findings"])
        and section["ok"] == (not section["findings"])
    )


def problems_found(section: dict) -> str:
    count = len(section["findings"])
    more = " or more" if section["truncated"] else ""
    return f"{count}{more} problem{'' if count == 1 else 's'} found"


def _is_finding(finding: object) -> bool:
    return (
        isinstance(finding, dict)
        and sorted(finding) == _FINDING_KEYS
        and all(isinstance(finding[key], str) for key in ("file", "message", "rule"))
        and (finding["line"] is None or type(finding["line"]) is int)
    )
