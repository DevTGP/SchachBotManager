"""Fixed protection limits of every bot process, the same for all languages (A14, E86).

They protect the server and are no game parameter; init tells the bot its memory limit.
"""

MEMORY_LIMIT_MIB = 1024
# nsjail, the runtime and its threads; enough for a JVM later, far too few for a fork bomb.
PIDS_LIMIT = 128
# The end of the bot's stderr the runner keeps for its log; the rest is read and dropped.
STDERR_TAIL_BYTES = 4096
