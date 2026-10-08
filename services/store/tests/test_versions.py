import pytest

from sbm_store import versions


@pytest.mark.parametrize(
    "text, parts",
    [("1.0.0", (1, 0, 0)), ("0.0.0", (0, 0, 0)), ("10.2.999", (10, 2, 999))],
)
def test_parse(text, parts):
    assert versions.parse(text) == parts


@pytest.mark.parametrize("text", ["1.0", "1.0.0.0", "01.0.0", "1000.0.0", "1.0.0 ", "v1.0.0", ""])
def test_parse_rejects(text):
    assert versions.parse(text) is None


def test_versions_compare_by_number():
    assert versions.parse("1.10.0") > versions.parse("1.9.9")


def test_next_patch():
    assert versions.next_patch("1.2.3") == "1.2.4"
    assert versions.next_patch("1.2.999") is None
    assert versions.next_patch("x") is None
