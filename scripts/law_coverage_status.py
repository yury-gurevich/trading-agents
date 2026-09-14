"""Validate status cells in law coverage rows.

Agent: tooling
Role: enforce non-green law-row classifications and their evidence text.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.law_coverage_model import TestPlanRow

ALLOWED_MARKS = ("🟩", "⬜", "🧱", "📜", "⛔")
STRUCTURAL_TOKENS = (
    "dependencies.md",
    "probes/checks.py",
    "import-linter",
    "check_",
    "module header",
)
EMPTY_TEST_TEXT = frozenset({"", "-", "—", "_tbd_", "tbd", "n/a", "none"})


def row_status_errors(row: TestPlanRow) -> tuple[str, ...]:
    """Return status/evidence errors for one parsed test-plan row."""
    errors: list[str] = []
    if not any(mark in row.status_text for mark in ALLOWED_MARKS):
        errors.append("row status has no recognized law mark")
        return tuple(errors)
    if "🧱" in row.status_text:
        errors.extend(_structural_errors(row))
    if "📜" in row.status_text:
        errors.extend(_charter_errors(row))
    return tuple(errors)


def _structural_errors(row: TestPlanRow) -> tuple[str, ...]:
    text = row.test_text.strip()
    lowered = text.lower()
    errors: list[str] = []
    if _empty(text):
        errors.append("structural row names no gate, probe, or charter")
    elif not any(token in lowered for token in STRUCTURAL_TOKENS):
        errors.append("structural row names no recognized gate/probe")
    return tuple(errors)


def _charter_errors(row: TestPlanRow) -> tuple[str, ...]:
    text = row.test_text.strip()
    if _empty(text) or "charter:" not in text.lower():
        return ("charter row states no unfalsifiable reason",)
    return ()


def _empty(text: str) -> bool:
    return text.strip().lower().strip("`") in EMPTY_TEST_TEXT
