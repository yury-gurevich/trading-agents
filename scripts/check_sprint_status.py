"""Classify declared sprint statuses without changing their source documents.

Agent: tooling
Role: report each sprint document's declared build status and ratchet refusals.
External I/O: reads docs/sprints Markdown files and writes reports to stdout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Final

# Run directly (`python scripts/check_sprint_status.py`) only `scripts/` is on
# sys.path, not the repo root, so the sibling import below needs the root first.
# Same shape as scripts/audit_broker_graph.py.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.sprint_status_report import (  # noqa: E402
    relative_path,
    render_report,
)
from scripts.sprint_status_types import (  # noqa: E402
    Baseline,
    CanonicalStatus,
    Classification,
    DocumentStatus,
    GateResult,
    Status,
    StatusReport,
)

_STATUS_MARKER: Final = "**Status:**"
_EXCLUDED_FILENAMES: Final = frozenset(
    {"INDEX.md", "README.md", "_TEMPLATE.md", "status-unmapped.md"}
)

_SYNONYMS: Final[dict[str, CanonicalStatus]] = {
    "spec": "SPEC",
    "planned": "SPEC",
    "queued": "SPEC",
    "ready": "SPEC",
    "built": "BUILT",
    "implemented": "BUILT",
    "merged": "MERGED",
    "shipped": "MERGED",
}


_BASELINE: Final = Baseline(unmapped=20, missing=20)


def classify_status_line(line: str) -> Classification:
    """Classify only the first word after the status marker."""
    remainder = line.removeprefix(_STATUS_MARKER).lstrip()
    match = re.match(r"(?P<token>\S+)(?P<evidence>.*)", remainder)
    if match is None:
        return Classification(status="UNMAPPED", evidence="")
    status = _SYNONYMS.get(match.group("token").casefold(), "UNMAPPED")
    return Classification(status=status, evidence=match.group("evidence"))


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


def check_root(root: Path, baseline: Baseline | None = None) -> GateResult:
    """Return errors only when a refusal count grows beyond its baseline."""
    report = scan_root(root)
    allowed = baseline if baseline is not None else _baseline_for(report.root)
    errors = (
        (_growth_error(report, "UNMAPPED", allowed.unmapped),)
        if report.count("UNMAPPED") > allowed.unmapped
        else ()
    )
    if report.count("MISSING") > allowed.missing:
        errors += (_growth_error(report, "MISSING", allowed.missing),)
    return GateResult(report=report, errors=errors)


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


def _baseline_for(root: Path) -> Baseline:
    return _BASELINE if root == _ROOT.resolve() else Baseline()


def _growth_error(report: StatusReport, status: Status, baseline: int) -> str:
    paths = ", ".join(
        relative_path(report, entry)
        for entry in report.entries
        if entry.status == status
    )
    return (
        f"[FAIL] {status} count {report.count(status)} exceeds baseline {baseline}: "
        f"{paths}"
    )


def _configure_stdout() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    _configure_stdout()
    raise SystemExit(main(sys.argv[1:]))
