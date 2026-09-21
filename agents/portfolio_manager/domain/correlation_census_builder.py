"""Build correlation census records from issuer comparisons.

Agent: portfolio_manager
Role: compare a candidate against held issuers and construct a correlation census.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.correlation_census import (
    CorrelationCensus,
    IssuerComparison,
    SkippedPair,
)
from agents.portfolio_manager.domain.correlation_ramp import rounded_contribution

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping


def build_census(
    *,
    candidate_ticker: str,
    candidate_issuer: str,
    issuer_keys: Iterable[str],
    issuer_tickers: Mapping[str, tuple[str, ...]],
    pair: Callable[[str, str], tuple[float | None, int]],
    threshold: float,
    min_bars: int,
    ceiling: float = 0.90,
) -> CorrelationCensus:
    """Compare the candidate against every held issuer and record each result."""
    comparisons: list[IssuerComparison] = []
    skipped: list[SkippedPair] = []
    for held in sorted(issuer_keys):
        if held == candidate_issuer:
            continue
        comparison = _compare(
            candidate_ticker,
            held,
            issuer_tickers,
            pair,
            min_bars,
            threshold,
            ceiling,
        )
        if comparison.overlap_bars < min_bars:
            skipped.append(
                SkippedPair(
                    issuer=comparison.issuer,
                    overlap_bars=comparison.overlap_bars,
                )
            )
            continue
        comparisons.append(comparison)
    return CorrelationCensus(
        comparisons=tuple(comparisons),
        skipped=tuple(skipped),
        threshold=threshold,
        ceiling=ceiling,
    )


def _compare(
    candidate_ticker: str,
    held_issuer: str,
    issuer_tickers: Mapping[str, tuple[str, ...]],
    pair: Callable[[str, str], tuple[float | None, int]],
    min_bars: int,
    threshold: float,
    ceiling: float,
) -> IssuerComparison:
    best: float | None = None
    widest = 0
    for held_ticker in issuer_tickers.get(held_issuer, ()):
        corr, overlap = pair(candidate_ticker, held_ticker)
        widest = max(widest, overlap)
        if overlap < min_bars or corr is None:
            continue
        best = corr if best is None else max(best, corr)
    return IssuerComparison(
        issuer=held_issuer,
        correlation=best,
        overlap_bars=widest,
        contribution=rounded_contribution(best, floor=threshold, ceiling=ceiling),
    )
