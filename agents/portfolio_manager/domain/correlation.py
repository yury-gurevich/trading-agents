"""Correlated-cluster concentration gate for Portfolio Manager.

Agent: portfolio_manager
Role: compute pairwise return correlation from run MarketData already on the graph.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.correlation_census import (
    CorrelationCensus,
    build_census,
)
from agents.portfolio_manager.domain.correlation_math import (
    pair_correlation,
    returns_by_ticker,
)
from agents.portfolio_manager.domain.issuer import issuer_key
from contracts.portfolio_manager import GateOutcome, GateStatus

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date

    from contracts.analyst import Recommendation
    from contracts.provider import OHLCVBar

_ZERO = Decimal("0")


@dataclass
class CorrelationBook:
    """Cached return series and pairwise correlations for one PM evaluation."""

    bars: tuple[OHLCVBar, ...]
    issuer_map: Mapping[str, str]
    lookback_days: int
    threshold: float
    max_cluster_pct: float | None
    min_bars: int
    _returns: dict[str, dict[date, float]] = field(init=False)
    _pair_cache: dict[tuple[str, str], tuple[float | None, int]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Build ticker return series once for the run."""
        self._returns = returns_by_ticker(self.bars, self.lookback_days)

    def outcomes(
        self,
        item: Recommendation,
        cost: Decimal,
        portfolio_value: Decimal,
        *,
        issuer_values: Mapping[str, Decimal],
        issuer_tickers: Mapping[str, tuple[str, ...]],
    ) -> tuple[GateOutcome, ...]:
        """Return the correlated-cluster outcome for this tentative order."""
        if self.max_cluster_pct is None:
            return ()
        issuer = issuer_key(item.ticker, self.issuer_map)
        census = build_census(
            candidate_ticker=item.ticker,
            candidate_issuer=issuer,
            issuer_keys=issuer_values,
            issuer_tickers=issuer_tickers,
            pair=self._pair,
            threshold=self.threshold,
            min_bars=self.min_bars,
        )
        if census.all_pairs_unusable():
            return (self._not_evaluated(item.ticker, census),)
        cluster = {issuer, *census.clustered()}
        value = cost + issuer_values.get(issuer, _ZERO)
        value += sum(issuer_values.get(key, _ZERO) for key in cluster if key != issuer)
        threshold_value = Decimal(str(self.max_cluster_pct)) * portfolio_value
        return (
            GateOutcome(
                name="correlated_cluster_pct",
                value=_ratio(value, portfolio_value),
                threshold=float(self.max_cluster_pct),
                outcome=(
                    GateStatus.PASSED if value <= threshold_value else GateStatus.FAILED
                ),
                detail=(
                    f"candidate_issuer={issuer}; "
                    f"cluster_issuers={','.join(sorted(cluster))}; "
                    f"{census.detail()}; "
                    f"cluster_value_usd={value:.2f}; "
                    f"portfolio_value_usd={portfolio_value:.2f}"
                ),
            ),
        )

    def _pair(self, left: str, right: str) -> tuple[float | None, int]:
        left_key = left.upper()
        right_key = right.upper()
        key = (left_key, right_key) if left_key <= right_key else (right_key, left_key)
        if key not in self._pair_cache:
            self._pair_cache[key] = pair_correlation(
                self._returns.get(key[0], {}), self._returns.get(key[1], {})
            )
        return self._pair_cache[key]

    def _not_evaluated(
        self, candidate_ticker: str, census: CorrelationCensus
    ) -> GateOutcome:
        first = census.first_skipped()
        held_issuer = "none" if first is None else first.issuer
        observed = 0 if first is None else first.overlap_bars
        return GateOutcome(
            name="correlated_cluster_pct",
            value=float(census.max_skipped_overlap()),
            threshold=float(self.min_bars),
            outcome=GateStatus.NOT_EVALUATED,
            detail=(
                "missing_input=overlapping_return_bars; "
                f"candidate_ticker={candidate_ticker}; held_issuer={held_issuer}; "
                f"observed_bars={observed}; min_correlation_bars={self.min_bars}; "
                f"{census.detail()}"
            ),
        )


def _ratio(numerator: Decimal, denominator: Decimal) -> float:
    return 0.0 if denominator <= 0 else float(numerator / denominator)
