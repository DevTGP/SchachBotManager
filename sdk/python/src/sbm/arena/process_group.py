"""All processes of one bot, to freeze it outside its turn and to end it completely (E67).

POPEN_OPTIONS go to subprocess.Popen; ProcessGroup(pid) is created right after the start and
offers suspend, resume, kill and close. Errors are OSError.
"""

import sys

if sys.platform == "win32":
    from sbm.arena.windows_job import POPEN_OPTIONS, ProcessGroup
else:
    from sbm.arena.posix_group import POPEN_OPTIONS, ProcessGroup

__all__ = ["POPEN_OPTIONS", "ProcessGroup"]
