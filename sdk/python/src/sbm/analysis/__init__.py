"""Static analysis of Python bots (statische-analyse.md): the same check as on the server."""

from sbm.analysis.analyzer import analyze
from sbm.analysis.project import Selection, check_project, select_files
from sbm.analysis.report import Finding, Report
from sbm.analysis.rules import Rules, load_rules

__all__ = [
    "Finding",
    "Report",
    "Rules",
    "Selection",
    "analyze",
    "check_project",
    "load_rules",
    "select_files",
]
