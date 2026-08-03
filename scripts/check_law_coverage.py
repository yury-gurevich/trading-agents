"""Pre-commit guard for agent-law coverage bookkeeping.

Agent: tooling
Role: ensure green law rows cite live tests and roll-up counters match the plans.
External I/O: filesystem reads of laws, test plans, roll-ups, and test files.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.law_coverage_docs import (  # noqa: E402
    discover_agent_books,
    parse_rollup_claims,
)
from scripts.law_coverage_tests import TestResolver, extract_citations  # noqa: E402

if TYPE_CHECKING:
    from scripts.law_coverage_model import AgentBook, Resolution, TestPlanRow

ROLLUP_PATHS = ("docs/laws/ledger.md", "docs/laws/INDEX.md")


@dataclass
class CoverageReport:
    """The checker result accumulated across the whole law book."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether no hard-fail assertion was violated."""
        return not self.errors


def check_root(root: Path) -> CoverageReport:
    """Check all law books rooted at ``root``."""
    report = CoverageReport()
    resolver = TestResolver(root)
    books = discover_agent_books(root)
    derived: dict[str, tuple[int, int]] = {}
    missing_by_agent: dict[str, list[str]] = {}

    for book in books:
        _check_book(book, resolver, report)
        derived[book.agent] = _derived_counter(book)
        missing = sorted(book.law_ids - {row.clause_id for row in book.rows})
        if missing:
            missing_by_agent[book.agent] = missing

    _check_rollups(root, derived, report)
    _add_missing_row_warnings(missing_by_agent, report)
    return report


def main(argv: list[str]) -> int:
    """Run the law-coverage checker and return a shell status."""
    root = Path(argv[0]).resolve() if argv else Path.cwd()
    report = check_root(root)
    for line in [*report.errors, *report.warnings]:
        print(line)
    return 0 if report.ok else 1


def _check_book(
    book: AgentBook,
    resolver: TestResolver,
    report: CoverageReport,
) -> None:
    for row in book.rows:
        if row.clause_id not in book.law_ids:
            report.errors.append(
                _row_message(
                    row, f"orphan row has no matching clause in {book.laws_path}"
                )
            )
        if row.green:
            _check_green_row(row, resolver, report)


def _check_green_row(
    row: TestPlanRow,
    resolver: TestResolver,
    report: CoverageReport,
) -> None:
    citations = extract_citations(row.test_text)
    if not citations:
        report.errors.append(_row_message(row, "green row has no test citation"))
        return

    resolutions = [resolver.resolve(row.agent, citation) for citation in citations]
    ambiguous = [resolution for resolution in resolutions if resolution.ambiguous]
    for resolution in ambiguous:
        root = _root_from_plan_path(row.path)
        paths = ", ".join(_display_path(root, path) for path in resolution.ambiguous)
        report.errors.append(
            _row_message(
                row,
                f"ambiguous citation {resolution.citation.raw!r} resolves to {paths}",
            )
        )
    if ambiguous:
        return

    targets = [target for resolution in resolutions for target in resolution.targets]
    if not targets:
        missing = ", ".join(_missing_detail(resolution) for resolution in resolutions)
        report.errors.append(
            _row_message(row, f"green row cites no live test: {missing}")
        )
        return

    citing = [
        target
        for target in targets
        if _docstring_cites(target.docstring, row.clause_id)
    ]
    if not citing:
        root = _root_from_plan_path(row.path)
        resolved = ", ".join(
            f"{_display_path(root, target.path)}::{target.name}" for target in targets
        )
        report.errors.append(
            _row_message(
                row,
                f"no resolved test docstring names {row.clause_id}: {resolved}",
            )
        )


def _check_rollups(
    root: Path,
    derived: dict[str, tuple[int, int]],
    report: CoverageReport,
) -> None:
    for raw_path in ROLLUP_PATHS:
        path = root / raw_path
        claims = parse_rollup_claims(path)
        for agent, (green, total) in derived.items():
            claim = claims.get(agent)
            if claim is None:
                report.errors.append(
                    f"[FAIL] {raw_path}: missing roll-up row for {agent}"
                )
                continue
            if (claim.green, claim.total) != (green, total):
                report.errors.append(
                    f"[FAIL] {_display_path(root, claim.path)}:{claim.line_number}: "
                    f"{agent} claims {claim.green} / {claim.total}; "
                    f"derived {green} / {total}"
                )


def _add_missing_row_warnings(
    missing_by_agent: dict[str, list[str]],
    report: CoverageReport,
) -> None:
    missing_total = sum(len(values) for values in missing_by_agent.values())
    if missing_total == 0:
        return
    report.warnings.append(
        f"[WARN] law coverage: {missing_total} clause(s) have no test-plan row "
        "(assertion E warn-only)"
    )
    for agent, missing in sorted(missing_by_agent.items()):
        report.warnings.append(
            f"[WARN] agents/{agent}/laws/test-plan.md: {len(missing)} missing row(s): "
            f"{', '.join(missing)}"
        )


def _derived_counter(book: AgentBook) -> tuple[int, int]:
    """Return proven clauses over declared clauses — never test-plan rows.

    The roll-up column is headed "Clauses green / total", so the denominator is
    the constitution (`laws.md`), not the bookkeeping that tracks it. Counting
    rows instead would drop every clause that has no row out of the denominator
    entirely — the defect this checker exists to surface: a clause with no row
    would stop being unproven and simply stop being counted.

    The numerator is distinct *clauses* with at least one green row, because a
    clause may carry several rows and must not be able to count more than once.
    """
    return len({row.clause_id for row in book.rows if row.green}), len(book.law_ids)


def _docstring_cites(docstring: str, clause_id: str) -> bool:
    return clause_id in docstring


def _missing_detail(resolution: Resolution) -> str:
    if resolution.missing is None:
        return resolution.citation.raw
    return f"{resolution.citation.raw} ({resolution.missing})"


def _row_message(row: TestPlanRow, message: str) -> str:
    root = _root_from_plan_path(row.path)
    return (
        f"[FAIL] {_display_path(root, row.path)}:{row.line_number}: "
        f"{row.clause_id} {message}"
    )


def _root_from_plan_path(path: Path) -> Path:
    return path.parents[3]


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
