"""The commands of the runtimes in the jail; the jail itself is tested in sandbox/ (E227)."""

from sbm.analysis.upload import CSHARP, JAVASCRIPT, PYTHON

from sbm_runner.sandbox.runtimes import NODE_FLAGS, RUNTIMES


def test_python_runs_the_analysis_isolated_from_the_bot():
    python = RUNTIMES[PYTHON]
    assert python.config == "python.cfg"
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


def test_node_always_runs_with_its_flags():
    node = RUNTIMES[JAVASCRIPT]
    assert node.config == "javascript.cfg"
    assert "--permission" in NODE_FLAGS
    assert "--allow-fs-write" not in " ".join(NODE_FLAGS)
    for command in (list(node.start), node.analysis("bot.js"), list(node.self_check)):
        assert command[: 1 + len(NODE_FLAGS)] == ["/usr/local/bin/node", *NODE_FLAGS]
    assert node.analysis("main.mjs")[-4:] == ["--json", "--entry", "main.mjs", "/bot"]
    assert node.build == ()


def test_only_csharp_builds():
    assert [language for language, runtime in RUNTIMES.items() if runtime.build] == [CSHARP]
    assert RUNTIMES[CSHARP].analyzer == ()
