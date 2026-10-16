"""The commands of the runtimes in the jail; the jail itself is tested in sandbox/ (E207)."""

from sbm_runner.sandbox.runtimes import JAVASCRIPT, NODE_FLAGS, PYTHON, REFERENCE, RUNTIMES


def test_python_runs_the_analysis_isolated_from_the_bot():
    python = RUNTIMES[PYTHON]
    assert python.config == "python.cfg"
    assert python.bot("/bot/bot.py") == ["/usr/local/bin/python3", "/bot/bot.py"]
    assert python.analysis("bot.py") == [
        "/usr/local/bin/python3",
        "-I",
        "-m",
        "sbm.analysis",
        "--json",
        "--entry",
        "bot.py",
        "/bot",
    ]
    assert python.label({"python": "3.14.8", "sdk": "0.4.0"}) == "python 3.14.8"


def test_node_always_runs_with_its_flags():
    node = RUNTIMES[JAVASCRIPT]
    assert node.config == "javascript.cfg"
    assert "--permission" in NODE_FLAGS
    assert "--allow-fs-write" not in " ".join(NODE_FLAGS)
    for command in (node.bot("/bot/bot.js"), node.analysis("bot.js"), node.check()):
        assert command[: 1 + len(NODE_FLAGS)] == ["/usr/local/bin/node", *NODE_FLAGS]
    assert node.analysis("main.mjs")[-4:] == ["--json", "--entry", "main.mjs", "/bot"]
    assert node.label({"node": "24.1.0", "sdk": "0.4.0"}) == "node 24.1.0"


def test_the_reference_bots_are_python_bots():
    assert REFERENCE is RUNTIMES[PYTHON]
