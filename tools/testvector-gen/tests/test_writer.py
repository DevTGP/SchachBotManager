import json

from testvector_gen.writer import render


def test_one_vector_per_line():
    text = render("s.json", "Ä description", [{"id": "a", "args": [1, 2]}, {"id": "b"}])
    assert text == (
        "{\n"
        '  "$schema": "s.json",\n'
        '  "description": "Ä description",\n'
        '  "vectors": [\n'
        '    {"id": "a", "args": [1, 2]},\n'
        '    {"id": "b"}\n'
        "  ]\n"
        "}\n"
    )
    assert json.loads(text)["vectors"][1] == {"id": "b"}
