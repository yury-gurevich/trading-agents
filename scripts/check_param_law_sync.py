"""Check that agent PARAM tables match their Pydantic settings fields.

Agent: tooling
Role: provide the command-line entrypoint for PARAM/settings reconciliation.
External I/O: filesystem reads through scripts.param_law_sync and stdout reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.param_law_sync import check_root  # noqa: E402


def main(argv: list[str]) -> int:
    root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    report = check_root(root)
    for line in [*report.errors, *report.warnings]:
        print(line)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
