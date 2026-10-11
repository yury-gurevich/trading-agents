"""Check that every live tracker is within the byte limit its charter declares.

Agent: tooling
Role: fail the gate when a tracker named under OPS-TRIM is over its limit.
External I/O: reads the housekeeping charter and the trackers it names; writes
reports to stdout.

The limits live in one place, the table under `## OPS-TRIM` in the housekeeping
charter. This script reads that table and holds no number of its own, so the
rule the operator reads and the rule the gate enforces cannot drift apart. A
table it cannot read in full is a failure, never an empty pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHARTER = "ops/departments/housekeeping/charter.md"
SECTION = "## OPS-TRIM"
BYTES_PER_KB = 1000
WARN_PERCENT = 90

_PATH_CELL = re.compile(r"`([^`]+)`")
_LIMIT_CELL = re.compile(r"(\d+) KB")
_RULE_CELL = re.compile(r":?-+:?")


class CharterError(ValueError):
    """The charter's limit table is absent or holds a row that cannot be read."""


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [n for n, line in enumerate(lines) if line.startswith(SECTION)]
    if len(starts) != 1:
        raise CharterError(f"expected one '{SECTION}' section, found {len(starts)}")
    body = lines[starts[0] + 1 :]
    ends = [n for n, line in enumerate(body) if line.startswith("## ")]
    return body[: ends[0]] if ends else body


def read_limits(text: str) -> dict[str, int]:
    """Return tracker path -> limit in bytes, from the table under OPS-TRIM."""
    body = _section(text)
    heads = [
        n
        for n, line in enumerate(body)
        if line.startswith("|") and _cells(line)[:2] == ["Tracker", "Limit"]
    ]
    if len(heads) != 1:
        raise CharterError(f"expected one Tracker | Limit table, found {len(heads)}")
    limits: dict[str, int] = {}
    for line in body[heads[0] + 1 :]:
        if not line.startswith("|"):
            break
        cells = _cells(line)
        if all(_RULE_CELL.fullmatch(cell) for cell in cells):
            continue
        path = _PATH_CELL.fullmatch(cells[0])
        limit = _LIMIT_CELL.fullmatch(cells[1]) if len(cells) > 1 else None
        if path is None or limit is None or int(limit.group(1)) == 0:
            raise CharterError(f"cannot read the limit row: {line.strip()[:80]}")
        if path.group(1) in limits:
            raise CharterError(f"{path.group(1)} is listed twice")
        limits[path.group(1)] = int(limit.group(1)) * BYTES_PER_KB
    if not limits:
        raise CharterError("the Tracker | Limit table has no rows")
    return limits


def stored_size(path: Path) -> int:
    """Count the bytes git stores for the file: line ends as LF."""
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def _report(root: Path, name: str, limit: int) -> bool:
    """Print one tracker's verdict and return whether it fails the gate."""
    path = root / name
    if not path.is_file():
        sys.stdout.write(f"[FAIL] {name}: named in {CHARTER} and not found.\n")
        return True
    size = stored_size(path)
    if size > limit:
        sys.stdout.write(
            f"[FAIL] {name}: {size:,} of {limit:,} bytes, over by {size - limit:,}. "
            f"Run the tracker trim ({CHARTER}, OPS-TRIM); do not raise the limit.\n"
        )
        return True
    percent = size * 100 // limit
    label = "WARN" if percent >= WARN_PERCENT else "OK"
    sys.stdout.write(f"[{label}] {name}: {size:,} of {limit:,} bytes ({percent} %)\n")
    return False


def main(argv: list[str]) -> int:
    """Check the trackers under the given root, or the working directory."""
    root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    charter = root / CHARTER
    try:
        limits = read_limits(charter.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, CharterError) as exc:
        sys.stdout.write(f"[FAIL] {CHARTER}: {exc}\n")
        return 1
    failed = [name for name, limit in limits.items() if _report(root, name, limit)]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
