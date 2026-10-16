"""The runtime of each language in the jail: how it starts, checks itself and builds (E86, E205)."""

from dataclasses import dataclass

from sbm.analysis.upload import CSHARP, PYTHON

_PYTHON = "/usr/local/bin/python3"
_PYTHON_CHECK = (
    "import json, sys, sbm, sbm.bots.material; "
    "print(json.dumps({'python': sys.version.split()[0], 'sdk': sbm.__version__}))"
)
_HOST = "/sbm/host"
_LAUNCHER = "/sbm/launch/sbm-launch.dll"


@dataclass(frozen=True)
class Runtime:
    """name is the key of the runtime's version in the self-check; config the nsjail file.

    start runs a bot, self_check prints {name: version, "sdk": version}; build and references
    compile a bot before its first game, for languages that need it.
    """

    name: str
    config: str
    start: tuple[str, ...]
    self_check: tuple[str, ...]
    build: tuple[str, ...] = ()
    references: tuple[str, ...] = ()


RUNTIMES: dict[str, Runtime] = {
    PYTHON: Runtime(
        name="python",
        config="python.cfg",
        start=(_PYTHON,),
        self_check=(_PYTHON, "-c", _PYTHON_CHECK),
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
