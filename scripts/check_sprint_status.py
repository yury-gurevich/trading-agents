"""Check that every sprint document declares its build status, and the README agrees.

Agent: tooling
Role: report each sprint document's declared build status and fail on any refusal.
External I/O: reads docs/sprints Markdown files and writes reports to stdout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Final, cast

# Run directly (`python scripts/check_sprint_status.py`) only `scripts/` is on
# sys.path, not the repo root, so the sibling import below needs the root first.
# Same shape as scripts/audit_broker_graph.py.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.sprint_status_index import leading_token, readme_cells  # noqa: E402
from scripts.sprint_status_report import (  # noqa: E402
    relative_path,
    render_report,
)
from scripts.sprint_status_types import (  # noqa: E402
    CanonicalStatus,
    Classification,
    DocumentStatus,
    GateResult,
    StatusReport,
)

_STATUS_MARKER: Final = "**Status:**"
_EXCLUDED_FILENAMES: Final = frozenset({"INDEX.md", "README.md", "_TEMPLATE.md"})
# Exactly the template's vocabulary, spelled exactly. Item 22 Part B migrated every
# synonym S224 accepted (`shipped`, `planned`, ...), so a new one is a refusal.
_VOCABULARY: Final[frozenset[CanonicalStatus]] = frozenset({"SPEC", "BUILT", "MERGED"})


def classify_status_line(line: str) -> Classification:
    """Classify only the first word after the status marker."""
    remainder = line.removeprefix(_STATUS_MARKER).lstrip()
    match = re.match(r"(?P<token>\S+)(?P<evidence>.*)", remainder)
    if match is None or match.group("token") not in _VOCABULARY:
        return Classification(status="UNMAPPED", evidence="")
    token = cast("CanonicalStatus", match.group("token"))
    return Classification(status=token, evidence=match.group("evidence"))


def scan_root(root: Path) -> StatusReport:
    """Read each sprint document once and retain its status line verbatim."""
    resolved = root.resolve()
    entries: list[DocumentStatus] = []
    for path in _sprint_documents(resolved):
        line = _first_status_line(path)
        if line is None:
            entries.append(
                DocumentStatus(path, status="MISSING", line=None, evidence="")
            )
            continue
        classification = classify_status_line(line)
        entries.append(
            DocumentStatus(
                path,
                status=classification.status,
                line=line,
                evidence=classification.evidence,
            )
        )
    return StatusReport(root=resolved, entries=tuple(entries))


def check_root(root: Path) -> GateResult:
    """Fail on any refusal, and on any README row that disagrees with its spec."""
    report = scan_root(root)
    errors = tuple(
        f"[FAIL] {entry.status}: {relative_path(report, entry)} — "
        f"{entry.line or '<no **Status:** line>'}"
        for entry in report.entries
        if entry.status in ("UNMAPPED", "MISSING")
    )
    return GateResult(report=report, errors=errors + _readme_disagreements(report))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("root", nargs="?")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    result = check_root(root)
    print(render_report(result.report))
    if args.report:
        return 0
    for error in result.errors:
        print(error)
    return 0 if result.ok else 1


def _readme_disagreements(report: StatusReport) -> tuple[str, ...]:
    readme = report.root / "docs" / "sprints" / "README.md"
    cells = readme_cells(readme) if readme.is_file() else {}
    errors: list[str] = []
    for entry in report.entries:
        if entry.status in ("UNMAPPED", "MISSING"):
            continue
        cell = cells.get(entry.path.name)
        if cell is None:
            errors.append(
                f"[FAIL] NO README ROW: {relative_path(report, entry)} "
                f"declares {entry.status}"
            )
        elif leading_token(cell) != entry.status:
            errors.append(
                f"[FAIL] README DISAGREES: {relative_path(report, entry)} declares "
                f"{entry.status}, its README row reads: {cell}"
            )
    return tuple(errors)


def _sprint_documents(root: Path) -> list[Path]:
    return [
        path
        for path in sorted((root / "docs" / "sprints").glob("*.md"))
        if path.name not in _EXCLUDED_FILENAMES
    ]


def _first_status_line(path: Path) -> str | None:
    return next(
        (
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith(_STATUS_MARKER)
        ),
        None,
    )


def _configure_stdout() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    _configure_stdout()
    raise SystemExit(main(sys.argv[1:]))
