"""Scanner ranking logic.

Agent: scanner
Role: turn surviving tickers into ranked Candidate payloads.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.scanner import Candidate

if TYPE_CHECKING:
    from agents.scanner.domain.filters import Survivor


def rank_survivors(
    survivors: tuple[Survivor, ...], *, cap: int
) -> tuple[Candidate, ...]:
    """Rank survivors by relative strength and trim to the candidate cap."""
    ordered = sorted(
        survivors,
        key=lambda item: (
            -item.metrics["relative_strength"],
            -item.metrics["average_volume"],
            item.ticker,
        ),
    )
    return tuple(
        Candidate(
            ticker=survivor.ticker,
            rank=rank,
            score=survivor.metrics["relative_strength"],
            survived_filters=survivor.survived_filters,
            metrics=survivor.metrics,
        )
        for rank, survivor in enumerate(ordered[:cap], start=1)
    )
