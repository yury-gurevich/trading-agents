"""Correlation gate edge-coverage tests.

Agent: portfolio_manager
Role: prove disabled, same-issuer, and degenerate-correlation paths.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from agents.portfolio_manager.domain.correlation import CorrelationBook
from agents.portfolio_manager.domain.correlation_math import (
    pair_correlation,
    returns_by_ticker,
)
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio
from agents.portfolio_manager.tests.s184_helpers import SECTORS, buy
from contracts.common import Money
from contracts.provider import OHLCVBar


def test_disabled_cluster_gate_emits_no_outcome() -> None:
    """PM-NEV-08: max_correlated_cluster_pct=None disables only this gate."""
    book = CorrelationBook((), {}, 120, 0.70, None, 60)

    outcomes = book.outcomes(
        buy("AAPL"),
        Decimal("1000.00"),
        Decimal("10000.00"),
        issuer_values={},
        issuer_tickers={},
    )

    assert outcomes == ()


def test_candidate_already_held_counts_same_issuer_without_pairing() -> None:
    """PM-NEV-07 / PM-NEV-08: an existing issuer adds exposure, not a new pair."""
    book = CorrelationBook(_bars(("AAPL",), days=66), {}, 120, 0.70, 0.25, 60)

    (outcome,) = book.outcomes(
        buy("AAPL"),
        Decimal("500.00"),
        Decimal("10000.00"),
        issuer_values={"AAPL": Decimal("1000.00")},
        issuer_tickers={"AAPL": ("AAPL",)},
    )

    assert outcome.outcome == "passed"
    assert outcome.value == 0.15
    assert "cluster_issuers=AAPL" in outcome.detail


def test_degenerate_pair_does_not_expand_cluster() -> None:
    """PM-NEV-08: undefined correlation is evaluated but not treated as correlated."""
    portfolio = cash_portfolio(
        "10000.00",
        {"AAPL": 10},
        position_values={"AAPL": Money(amount=Decimal("1000.00"))},
    )

    approved, rejected = evaluate_recommendations(
        (buy("MSFT"),),
        {"MSFT": Money(amount=Decimal("100.00"))},
        portfolio,
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=SECTORS,
        max_sector_pct=Decimal("0.50"),
        max_names_per_sector=3,
        correlation_bars=(*_flat_bars("AAPL", days=66), *_bars(("MSFT",), days=66)),
        correlation_lookback_days=120,
        correlation_threshold=0.70,
        max_correlated_cluster_pct=0.25,
        min_correlation_bars=60,
    )

    cluster = next(
        item
        for item in approved[0].gate_report
        if item.name == "correlated_cluster_pct"
    )
    assert rejected == ()
    assert cluster.outcome == "passed"
    assert "cluster_issuers=MSFT" in cluster.detail


def test_correlation_math_handles_empty_and_disjoint_inputs() -> None:
    """PM-NEV-08: empty or disjoint run bars do not invent correlation."""
    assert returns_by_ticker((), 120) == {}
    assert pair_correlation({date(2026, 1, 1): 0.01}, {date(2026, 1, 2): 0.02}) == (
        None,
        0,
    )


def test_return_math_ignores_bars_outside_lookback() -> None:
    """PM-NEV-08: measured correlation uses the configured lookback window."""
    rows = (_bar("AAPL", 0, 50.0), _bar("AAPL", 20, 100.0), _bar("AAPL", 21, 101.0))

    result = returns_by_ticker(rows, 10)

    assert result.keys() == {"AAPL"}
    assert result["AAPL"] == {date(2026, 1, 22): pytest.approx(0.01)}


def _bars(tickers: tuple[str, ...], *, days: int) -> tuple[OHLCVBar, ...]:
    rows: list[OHLCVBar] = []
    for ticker_index, ticker in enumerate(tickers):
        close = 100.0 + ticker_index
        for offset in range(days):
            if offset:
                close *= 1.01 if offset % 2 else 0.995
            rows.append(_bar(ticker, offset, close))
    return tuple(rows)


def _flat_bars(ticker: str, *, days: int) -> tuple[OHLCVBar, ...]:
    return tuple(_bar(ticker, offset, 100.0) for offset in range(days))


def _bar(ticker: str, offset: int, close: float) -> OHLCVBar:
    day = date(2026, 1, 1) + timedelta(days=offset)
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=1_000_000,
    )
