"""Answers init with a line of 100 KiB, longer than the protocol allows (sandbox.md).

Without the SDK, which would never write such a line.
"""

import sys

sys.stdin.readline()
sys.stdout.write("x" * (100 << 10) + "\n")
sys.stdout.flush()
sys.stdin.read()
