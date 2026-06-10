"""Pre-commit guard: every source module carries a coding-agent header.

Agent: tooling
Role: enforce that each module's docstring declares `Agent:` and `Role:`, so a
      coding agent can read a file's purpose and ownership without parsing code.
External I/O: filesystem (reads source files).

The header is a plain docstring with labelled lines, e.g.::

    \"\"\"One-line summary.

    Agent: <name|kernel|contracts|tooling>
    Role: <what this module does>
    External I/O: <systems | none>
    \"\"\"
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REQUIRED_FIELDS = ("Agent:", "Role:")
_SCOPED_PREFIXES = (
    "kernel/",
    "contracts/",
    "agents/",
    "orchestration/",
    "surfaces/",
    "scripts/",
)


def _is_checked_path(path: Path) -> bool:
    """Return whether a path must carry a coding-agent header."""
    normalized = path.as_posix()
    if normalized.endswith("__init__.py") or "alembic/versions" in normalized:
        return False
    return normalized.startswith(_SCOPED_PREFIXES) and normalized.endswith(".py")


def _missing_fields(path: Path) -> list[str]:
    """Return required header fields absent from a module's docstring."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return ["<syntax error>"]
    docstring = ast.get_docstring(tree) or ""
    return [field for field in REQUIRED_FIELDS if field not in docstring]


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
    """Check files and return a pre-commit-compatible status."""
    failed = False
    for raw_path in argv:
        for path in _iter_checked_files(raw_path):
            missing = _missing_fields(path)
            if missing:
                sys.stdout.write(
                    f"[FAIL] {path}: header missing {', '.join(missing)}\n"
                )
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
