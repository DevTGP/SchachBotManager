"""load_data: plain file names from SBM_DATA_DIR or data next to the main file (E62)."""

import sys
import types

import pytest

import sbm


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SBM_DATA_DIR", str(tmp_path))
    (tmp_path / "book.bin").write_bytes(b"\x00\x01book")
    (tmp_path / "folder").mkdir()
    return tmp_path


def test_reads_bytes(data_dir):
    assert sbm.load_data("book.bin") == b"\x00\x01book"


@pytest.mark.parametrize(
    "name", ["", ".", "..", "a/b", "/book.bin", r"a\b", r"..\book.bin", "a\0b"]
)
def test_rejects_paths(data_dir, name):
    with pytest.raises(sbm.InvalidArgumentError, match="load_data"):
        sbm.load_data(name)


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters exist only on Windows")
def test_rejects_drive(data_dir):
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.load_data("C:book.bin")


@pytest.mark.parametrize("name", ["missing.bin", "folder"])
def test_missing_file(data_dir, name):
    with pytest.raises(sbm.DataNotFoundError, match=name):
        sbm.load_data(name)


def test_wrong_type(data_dir):
    with pytest.raises(TypeError):
        sbm.load_data(b"book.bin")


def test_data_next_to_main_file(tmp_path, monkeypatch):
    monkeypatch.delenv("SBM_DATA_DIR", raising=False)
    main = types.ModuleType("__main__")
    main.__file__ = str(tmp_path / "my_bot.py")
    monkeypatch.setitem(sys.modules, "__main__", main)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "weights.txt").write_bytes(b"1 2 3")
    assert sbm.load_data("weights.txt") == b"1 2 3"
    with pytest.raises(sbm.DataNotFoundError):
        sbm.load_data("my_bot.py")
