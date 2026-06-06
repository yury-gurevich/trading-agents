"""Pre-commit guard for module size limits.

Agent: tooling
Role: keep modules small and readable — warn at 150 lines, hard-block at 200.
External I/O: filesystem (reads source files).

Clean start: no grandfathered files. Package markers and migration revisions are
exempt.
"""

from __future__ import annotations

import sys
from pathlib import Path

WARN_LIMIT = 150
FAIL_LIMIT = 200

_SCOPED_PREFIXES = (
    "kernel/",
    "contracts/",
    "agents/",
    "orchestration/",
    "surfaces/",
    "tests/",
)


def _is_checked_path(path: Path) -> bool:
    """Return whether a path is in the module-size enforcement scope."""
    normalized = path.as_posix()
    if "__init__.py" in normalized or "alembic/versions" in normalized:
        return False
    return normalized.startswith(_SCOPED_PREFIXES)


def _line_count(path: Path) -> int:
    """Count total lines in a UTF-8 Python source file."""
    return len(path.read_text(encoding="utf-8").splitlines())


def _iter_checked_files(raw_path: str) -> list[Path]:
    """Expand a pre-commit file argument or manual directory argument."""
    path = Path(raw_path)
    if not path.exists():
        return []
    if path.is_dir():
        return [
            child for child in sorted(path.rglob("*.py")) if _is_checked_path(child)
        ]
    if _is_checked_path(path):
        return [path]
    return []


def main(argv: list[str]) -> int:
    """Check staged Python files and return a pre-commit-compatible status."""
    failed = False
    for raw_path in argv:
        for path in _iter_checked_files(raw_path):
            count = _line_count(path)
            if count >= FAIL_LIMIT:
                sys.stdout.write(
                    f"[FAIL] {path}: {count} lines - exceeds the 200-line hard block. "
                    "Split before committing.\n"
                )
                failed = True
            elif count >= WARN_LIMIT:
                sys.stdout.write(
                    f"[WARN] {path}: {count} lines (warn 150, hard block 200)\n"
                )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
