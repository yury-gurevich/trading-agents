"""Encoding-safe PARAM report output (DL-276 D5).

Agent: tooling
Role: preserve exit semantics even when stdout cannot encode law symbols.
External I/O: stdout only.
"""

import sys


def safe_print(line: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    print(line.encode(encoding, errors="replace").decode(encoding))
