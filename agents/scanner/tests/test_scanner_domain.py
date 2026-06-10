"""Scanner domain ranking tests.

Agent: scanner
Role: verify deterministic scanner ranking edge cases.
External I/O: none.
"""

from __future__ import annotations

from agents.scanner.domain.filters import Survivor
from agents.scanner.domain.ranking import rank_survivors


def test_rank_survivors_breaks_numeric_ties_by_ticker_ascending() -> None:
    survivors = (
        _survivor("MSFT", relative_strength=0.10, average_volume=1_000_000.0),
        _survivor("AAPL", relative_strength=0.10, average_volume=1_000_000.0),
        _survivor("NVDA", relative_strength=0.09, average_volume=2_000_000.0),
    )

    ranked = rank_survivors(survivors, cap=3)

    assert [candidate.ticker for candidate in ranked] == ["AAPL", "MSFT", "NVDA"]


def _survivor(
    ticker: str, *, relative_strength: float, average_volume: float
) -> Survivor:
    return Survivor(
        ticker=ticker,
        survived_filters=("fixture",),
        metrics={
            "relative_strength": relative_strength,
            "average_volume": average_volume,
        },
    )
