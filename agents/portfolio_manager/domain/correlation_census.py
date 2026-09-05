"""Census of the comparisons behind one correlated-cluster gate outcome.

Agent: portfolio_manager
Role: record and render how many held issuers a correlation gate examined, so a
      cluster of one is distinguishable from a comparison that never happened.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

_TOP_BELOW = 3
_NONE = "none"
_UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class IssuerComparison:
    """One held issuer measured against the candidate ticker."""

    issuer: str
    correlation: float | None
    overlap_bars: int

    def render(self) -> str:
        """Render this comparison as ``ISSUER:correlation``."""
        if self.correlation is None:
            return f"{self.issuer}:{_UNMEASURED}"
        return f"{self.issuer}:{self.correlation:.4f}"


@dataclass(frozen=True)
class CorrelationCensus:
    """Every comparison the correlated-cluster gate performed for one candidate."""

    comparisons: tuple[IssuerComparison, ...]
    threshold: float

    def clustered(self) -> tuple[str, ...]:
        """Return the held issuers whose measured correlation reached the threshold."""
        return tuple(item.issuer for item in self._at_or_above())

    def detail(self) -> str:
        """Render the census as gate-detail fields."""
        return "; ".join(
            (
                f"examined_issuers={len(self.comparisons)}",
                f"correlated_issuers={_render(self._at_or_above())}",
                f"below_threshold_top={_render(self._below()[:_TOP_BELOW])}",
                f"correlation_threshold={self.threshold:.4f}",
                f"min_pair_overlap_bars={self._min_overlap()}",
            )
        )

    def _at_or_above(self) -> tuple[IssuerComparison, ...]:
        return self._ranked(
            item
            for item in self.comparisons
            if item.correlation is not None and item.correlation >= self.threshold
        )

    def _below(self) -> tuple[IssuerComparison, ...]:
        return self._ranked(
            item
            for item in self.comparisons
            if item.correlation is None or item.correlation < self.threshold
        )

    @staticmethod
    def _ranked(items: Iterable[IssuerComparison]) -> tuple[IssuerComparison, ...]:
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    item.correlation is None,
                    -(item.correlation or 0.0),
                    item.issuer,
                ),
            )
        )

    def _min_overlap(self) -> str:
        if not self.comparisons:
            return _NONE
        return str(min(item.overlap_bars for item in self.comparisons))


def build_census(
    *,
    candidate_ticker: str,
    candidate_issuer: str,
    issuer_keys: Iterable[str],
    issuer_tickers: Mapping[str, tuple[str, ...]],
    pair: Callable[[str, str], tuple[float | None, int]],
    threshold: float,
    min_bars: int,
) -> CorrelationCensus:
    """Compare the candidate against every held issuer and record each result."""
    comparisons = tuple(
        _compare(candidate_ticker, held, issuer_tickers, pair, min_bars)
        for held in sorted(issuer_keys)
        if held != candidate_issuer
    )
    return CorrelationCensus(comparisons=comparisons, threshold=threshold)


def _compare(
    candidate_ticker: str,
    held_issuer: str,
    issuer_tickers: Mapping[str, tuple[str, ...]],
    pair: Callable[[str, str], tuple[float | None, int]],
    min_bars: int,
) -> IssuerComparison:
    best: float | None = None
    widest = 0
    for held_ticker in issuer_tickers.get(held_issuer, ()):
        corr, overlap = pair(candidate_ticker, held_ticker)
        widest = max(widest, overlap)
        if overlap < min_bars or corr is None:
            continue
        best = corr if best is None else max(best, corr)
    return IssuerComparison(issuer=held_issuer, correlation=best, overlap_bars=widest)


def _render(items: tuple[IssuerComparison, ...]) -> str:
    return ",".join(item.render() for item in items) if items else _NONE
