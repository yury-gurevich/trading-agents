"""Scanner result builders.

Agent: scanner
Role: construct scan explanations from candidate sets and filter traces.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation

if TYPE_CHECKING:
    from contracts.scanner import Candidate, FilterTrace


def scan_explanation(
    candidates: tuple[Candidate, ...], trace: FilterTrace
) -> Explanation:
    """Return a human-readable scan explanation from the survivor set and trace."""
    if not candidates:
        return Explanation(
            summary="No candidates survived the scanner filters.",
            evidence_refs=("scanner.filters.core",),
        )
    return Explanation(
        summary=(
            f"{len(candidates)} candidates survived from {trace.evaluated} evaluated "
            "tickers using price, liquidity, relative-strength, beta, and "
            "earnings-window filters."
        ),
        evidence_refs=("scanner.filters.core",),
    )
