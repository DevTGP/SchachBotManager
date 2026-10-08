"""python -m sbm.analysis, the same as sbm-check; the runner calls it in the sandbox."""

import sys

from sbm.analysis.cli import main

sys.exit(main())
