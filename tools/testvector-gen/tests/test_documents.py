import json

from testvector_gen.documents import documents


def test_schema_paths_are_relative():
    for name, text in documents().items():
        schema = json.loads(text)["$schema"]
        expected = "perft.schema.json" if name == "perft.json" else "calls.schema.json"
        assert schema == "../" * name.count("/") + expected


def test_ids_unique_across_files():
    ids = [vector["id"] for text in documents().values() for vector in json.loads(text)["vectors"]]
    assert len(ids) == len(set(ids))
