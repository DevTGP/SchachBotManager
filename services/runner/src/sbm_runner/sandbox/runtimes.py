"""The runtime of each language in the jail: how it starts, checks itself, analyzes and builds.

Each runtime has its own root under /opt/sbm/runtimes and its own nsjail configuration
(E86, E205, E227).
"""

from dataclasses import dataclass

from sbm.analysis.upload import CSHARP, JAVASCRIPT, PYTHON

_PYTHON = "/usr/local/bin/python3"
_PYTHON_CHECK = (
    "import json, sys, sbm, sbm.bots.material; "
    "print(json.dumps({'python': sys.version.split()[0], 'sdk': sbm.__version__}))"
)

# Node keeps what the jail does not already forbid: no child processes, workers, WASI or
# inspector (--permission), no eval or new Function, no WebAssembly; the heap stays below the
# memory limit of the cgroup, so a full heap ends in a JavaScript error, not in the OOM killer.
NODE_FLAGS = (
    "--permission",
    "--allow-fs-read=*",
    "--allow-addons",
    "--disable-warning=SecurityWarning",
    "--disallow-code-generation-from-strings",
    "--no-expose-wasm",
    "--max-old-space-size=768",
)
_NODE = ("/usr/local/bin/node", *NODE_FLAGS)
_NODE_CHECK = (
    'import { version, Board } from "schachbotmanager"; new Board(); '
    "console.log(JSON.stringify({ node: process.versions.node, sdk: version }))"
)

_HOST = "/sbm/host"
_LAUNCHER = "/sbm/launch/sbm-launch.dll"


@dataclass(frozen=True)
class Runtime:
    """name is the key of the runtime's version in the self-check; config the nsjail file.

    start runs a bot, self_check prints {name: version, "sdk": version}; analyzer runs sbm-check
    for languages without a build; build and references compile a bot before its first game,
    for languages that need it.
    """

    name: str
    config: str
    start: tuple[str, ...]
    self_check: tuple[str, ...]
    analyzer: tuple[str, ...] = ()
    build: tuple[str, ...] = ()
    references: tuple[str, ...] = ()

    def analysis(self, entry: str) -> list[str]:
        """sbm-check over /bot as JSON."""
        return [*self.analyzer, "--json", "--entry", entry, "/bot"]


RUNTIMES: dict[str, Runtime] = {
    PYTHON: Runtime(
        name="python",
        config="python.cfg",
        start=(_PYTHON,),
        self_check=(_PYTHON, "-c", _PYTHON_CHECK),
        # -I keeps /bot off the module path, so no uploaded file can stand in for the analyzer.
        analyzer=(_PYTHON, "-I", "-m", "sbm.analysis"),
    ),
    JAVASCRIPT: Runtime(
        name="node",
        config="javascript.cfg",
        start=_NODE,
        self_check=(*_NODE, "--input-type=module", "-e", _NODE_CHECK),
        # The analyzer is a file of the runtime; Node resolves no module from /bot for it.
        analyzer=(*_NODE, "/node_modules/schachbotmanager/dist/analysis/bin.js"),
    ),
    CSHARP: Runtime(
        name="dotnet",
        config="csharp.cfg",
        start=(_HOST, _LAUNCHER),
        self_check=(_HOST, _LAUNCHER, "--versions"),
        build=(_HOST, "/sbm/build/sbm-build.dll"),
        references=("--references", "/sbm/refs/net", "--references", "/sbm/refs/sdk"),
    ),
}
