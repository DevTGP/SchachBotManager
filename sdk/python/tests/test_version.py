"""The package carries the version of the core (E36)."""

import importlib.metadata
import re

import sbm


def test_version_matches_core():
    assert sbm.__version__ == sbm.core_version()
    assert importlib.metadata.version("schachbotmanager") == sbm.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", sbm.__version__)
