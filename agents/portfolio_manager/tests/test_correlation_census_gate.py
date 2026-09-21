"""Correlation census gate-integration tests.

Agent: portfolio_manager
Role: prove the correlation census reaches gate outcomes with its applied weights.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from agents.portfolio_manager.domain.correlation import CorrelationBook
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.provider import OHLCVBar


def test_gate_detail_carries_the_census_beside_the_cluster() -> None:
    """PM-OBS-03: the census reaches the gate_report the deliberator reads."""
    book = CorrelationBook(
        (*_bars("AAPL", days=66), *_bars("MSFT", days=66, drift=1.01)),
        {},
        120,
        0.70,
        0.25,
        60,
    )

    outcomes = book.outcomes(
        buy("AAPL"),
        Decimal("500.00"),
        Decimal("10000.00"),
        issuer_values={"MSFT": Decimal("1000.00")},
        issuer_tickers={"MSFT": ("MSFT",)},
    )

    assert len(outcomes) == 1
    assert "examined_issuers=1" in outcomes[0].detail
    assert "min_pair_overlap_bars=65" in outcomes[0].detail
    assert "skipped_pairs=0" in outcomes[0].detail


def test_midpoint_correlation_contributes_half_the_held_issuer_value() -> None:
    """PM-NEV-08 / PM-OBS-03: ramp midpoint applies and renders a half weight."""
    book = CorrelationBook((), {}, 120, 0.50, 0.25, 60)
    book._pair_cache[("AMZN", "MSFT")] = (0.70, 120)

    outcome = book.outcomes(
        buy("AMZN"),
        Decimal("100.00"),
        Decimal("2000.00"),
        deployed_value=Decimal("2000.00"),
        issuer_values={"MSFT": Decimal("1000.00")},
        issuer_tickers={"MSFT": ("MSFT",)},
    )[0]

    assert outcome.value == 0.30
    assert "cluster_issuers=AMZN,MSFT" in outcome.detail
    assert "correlated_issuers=MSFT:0.7000:w0.5000" in outcome.detail
    assert "cluster_weight_total=0.5000" in outcome.detail
    assert "cluster_value_usd=600.00" in outcome.detail


def _bars(ticker: str, *, days: int, drift: float = 1.0) -> tuple[OHLCVBar, ...]:
    rows: list[OHLCVBar] = []
    close = 100.0
    for offset in range(days):
        if offset:
            close *= (1.01 if offset % 2 else 0.995) * drift
        day = date(2026, 1, 1) + timedelta(days=offset)
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=day,
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=1_000_000,
            )
        )
    return tuple(rows)
