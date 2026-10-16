"""The runtimes of the bots in the jail, one per language (E86, E227).

Each runtime has its own root under /opt/sbm/runtimes, its own nsjail configuration
<language>.cfg and its own analyzer (sbm-check), which also runs in the jail.
"""

from dataclasses import dataclass

PYTHON = "python"
JAVASCRIPT = "javascript"

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

_PYTHON_CHECK = (
    "import json, sys, sbm, sbm.bots.material; "
    "print(json.dumps({'python': sys.version.split()[0], 'sdk': sbm.__version__}))"
)
_NODE_CHECK = (
    'import { version, Board } from "schachbotmanager"; new Board(); '
    "console.log(JSON.stringify({ node: process.versions.node, sdk: version }))"
)


@dataclass(frozen=True)
class Runtime:
    """name and its version in the self-check label the runtime of a verified bot."""

    language: str
    name: str
    interpreter: tuple[str, ...]
    # The arguments before --json --entry ENTRY /bot.
    analyzer: tuple[str, ...]
    self_check: tuple[str, ...]

    @property
    def config(self) -> str:
        return f"{self.language}.cfg"

    def bot(self, *arguments: str) -> list[str]:
        return [*self.interpreter, *arguments]

    def analysis(self, entry: str) -> list[str]:
        return [*self.interpreter, *self.analyzer, "--json", "--entry", entry, "/bot"]

    def check(self) -> list[str]:
        return [*self.interpreter, *self.self_check]

    def label(self, versions: dict[str, str]) -> str:
        return f"{self.name} {versions[self.name]}"


RUNTIMES = {
    # -I keeps /bot off the module path, so no uploaded file can stand in for the analyzer.
    PYTHON: Runtime(
        language=PYTHON,
        name="python",
        interpreter=("/usr/local/bin/python3",),
        analyzer=("-I", "-m", "sbm.analysis"),
        self_check=("-c", _PYTHON_CHECK),
    ),
    # The analyzer is a file of the runtime; Node resolves no module from /bot for it.
    JAVASCRIPT: Runtime(
        language=JAVASCRIPT,
        name="node",
        interpreter=("/usr/local/bin/node", *NODE_FLAGS),
        analyzer=("/node_modules/schachbotmanager/dist/analysis/bin.js",),
        self_check=("--input-type=module", "-e", _NODE_CHECK),
    ),
}
# The reference bots are Python bots of the SDK.
REFERENCE = RUNTIMES[PYTHON]
