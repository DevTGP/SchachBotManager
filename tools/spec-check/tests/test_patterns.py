from pathlib import Path

from spec_check.patterns import check_patterns, find_patterns, pattern_problems


def test_finds_nested_patterns_but_not_properties_named_pattern():
    schema = {
        "properties": {
            "pattern": {"type": "string", "pattern": "^a(?!\\n)$"},
            "list": {"items": [{"pattern": "^b(?!\\n)$"}]},
        }
    }

    assert sorted(find_patterns(schema)) == ["^a(?!\\n)$", "^b(?!\\n)$"]


def test_accepts_portable_pattern():
    assert pattern_problems("^[0-9]+(?!\\n)$") == []


def test_accepts_unanchored_pattern():
    assert pattern_problems("^[a-h]") == []


def test_rejects_digit_class():
    assert len(pattern_problems("^[a-h]\\d(?!\\n)$")) == 1


def test_rejects_plain_end_anchor():
    assert len(pattern_problems("^[0-9]+$")) == 1


def test_reports_each_problem_with_its_file():
    path = Path("x.schema.json")

    problems = check_patterns({path: {"pattern": "^\\d$"}})

    assert [p.path for p in problems] == [path, path]
