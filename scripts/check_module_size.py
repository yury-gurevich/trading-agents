"""Pre-commit guard for module size limits.

Agent: tooling
Role: keep modules small and readable — warn at 150 lines, hard-block at 200.
External I/O: filesystem (reads source files).

Package markers and migration revisions are exempt. `scripts/` is in scope since
2026-09-23; the files that were already over the block when it came into scope
are frozen at their measured size in `module_size_baseline.py` and can only
shrink. Everything else starts clean.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.module_size_baseline import LEGACY_MAX_LINES  # noqa: E402

WARN_LIMIT = 150
FAIL_LIMIT = 200
BASELINE_FILE = "scripts/module_size_baseline.py"

_SCOPED_PREFIXES = (
    "kernel/",
    "contracts/",
    "agents/",
    "orchestration/",
    "surfaces/",
    "tests/",
    "scripts/",
)


def _is_checked_path(path: Path) -> bool:
    """Return whether a path is in the module-size enforcement scope."""
    normalized = _relative(path)
    if "__init__.py" in normalized:
        return False
    if normalized.startswith(_SCOPED_PREFIXES):
        return True
    # An absolute path outside the repo (a test fixture) still belongs to the
    # scope its own folder names, so the rules stay testable off-tree.
    return any(f"/{prefix}" in normalized for prefix in _SCOPED_PREFIXES)


def _line_count(path: Path) -> int:
    """Count total lines in a UTF-8 Python source file."""
    return len(path.read_text(encoding="utf-8").splitlines())


def _relative(path: Path) -> str:
    """Return the repo-relative posix path the baseline is keyed by."""
    try:
        return path.resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def _report(path: Path, count: int) -> bool:
    """Print one file's verdict and return whether it fails the gate."""
    name = _relative(path)
    ceiling = LEGACY_MAX_LINES.get(name)
    if ceiling is not None:
        if count > ceiling:
            sys.stdout.write(
                f"[FAIL] {name}: {count} lines - legacy ceiling is {ceiling} and this "
                f"list only shrinks. Split it, do not raise the number.\n"
            )
            return True
        if count < FAIL_LIMIT:
            sys.stdout.write(
                f"[FAIL] {name}: {count} lines is under the block - delete its entry "
                f"from {BASELINE_FILE} so it cannot grow back.\n"
            )
            return True
        sys.stdout.write(f"[LEGACY] {name}: {count} lines (ceiling {ceiling})\n")
        return False
    if count >= FAIL_LIMIT:
        sys.stdout.write(
            f"[FAIL] {name}: {count} lines - exceeds the 200-line hard block. "
            "Split before committing.\n"
        )
        return True
    if count >= WARN_LIMIT:
        sys.stdout.write(f"[WARN] {name}: {count} lines (warn 150, hard block 200)\n")
    return False


def _missing_baseline_entries(seen: set[str]) -> list[str]:
    """Return baselined paths that were in scope to check and did not appear."""
    return sorted(
        name
        for name in LEGACY_MAX_LINES
        if name not in seen and not (_ROOT / name).exists()
    )


def main(argv: list[str]) -> int:
    """Check staged Python files and return a pre-commit-compatible status."""
    failed = False
    seen: set[str] = set()
    for raw_path in argv:
        for path in _iter_checked_files(raw_path):
            seen.add(_relative(path))
            failed = _report(path, _line_count(path)) or failed
    for name in _missing_baseline_entries(seen):
        sys.stdout.write(
            f"[FAIL] {name}: baselined but no longer present - delete its entry "
            f"from {BASELINE_FILE}.\n"
        )
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
