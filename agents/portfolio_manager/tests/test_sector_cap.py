"""Sector-concentration cap tests.

Agent: portfolio_manager
Role: verify the per-sector deployment cap rejects over-concentrated orders, skips
      unknown sectors, and disables at 1.0 — as a unit and over the bus.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import (
    bar,
    cash_portfolio,
    evaluate_message,
    recommendation,
    recommendation_set,
    wire_pm,
)
from agents.portfolio_manager.tests.s184_helpers import correlated_bars
from contracts.common import Money, Provenance
from contracts.portfolio_manager import OrderIntentSet
from contracts.provider import MARKET_DATA_LABEL, DataQualityTrace, MarketData, OHLCVBar

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import OrderIntent, RejectedOrder


def _two_tech_buys(
    sectors: dict[str, str], max_sector_pct: Decimal
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    def rec(ticker: str, confidence: float) -> Recommendation:
        return recommendation(ticker, confidence=confidence).model_copy(
            update={"suggested_stop_pct": 0.05, "suggested_target_pct": 0.10}
        )

    recs = (rec("AAPL", 0.90), rec("MSFT", 0.80))
    prices = {
        "AAPL": Money(amount=Decimal("100.00")),
        "MSFT": Money(amount=Decimal("100.00")),
    }
    return evaluate_recommendations(
        recs,
        prices,
        cash_portfolio(
            "20000.00",
            {"OTHER": 1},
            position_values={"OTHER": Money(amount=Decimal("10000.00"))},
        ),
        max_position_pct=Decimal("0.05"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=sectors,
        max_sector_pct=max_sector_pct,
    )


def test_rejects_second_same_sector_order_over_cap() -> None:
    """PM-NEV-04: max_sector_pct gate rejects second same-sector order over cap."""
    # Each order deploys $1,000; the 0.15 cap allows $1,500 of "Tech".
    approved, rejected = _two_tech_buys(
        {"AAPL": "Tech", "MSFT": "Tech"}, Decimal("0.15")
    )
    assert [o.ticker for o in approved] == ["AAPL"]
    assert [(r.ticker, r.reason) for r in rejected] == [
        ("MSFT", "sector_concentration")
    ]


def test_approves_same_sector_within_cap() -> None:
    approved, rejected = _two_tech_buys(
        {"AAPL": "Tech", "MSFT": "Tech"}, Decimal("0.30")
    )
    assert {o.ticker for o in approved} == {"AAPL", "MSFT"}
    assert rejected == ()


def test_unknown_sector_is_not_evaluated() -> None:
    """PM-NEV-09: a missing sector label is not a silent cap pass."""
    approved, rejected = _two_tech_buys({"AAPL": "Tech"}, Decimal("0.15"))
    assert {o.ticker for o in approved} == {"AAPL"}
    assert [(item.ticker, item.reason) for item in rejected] == [
        ("MSFT", "sector_not_evaluated")
    ]


def test_max_sector_pct_of_one_disables_the_cap() -> None:
    approved, rejected = _two_tech_buys({"AAPL": "Tech", "MSFT": "Tech"}, Decimal("1"))
    assert {o.ticker for o in approved} == {"AAPL", "MSFT"}
    assert rejected == ()


def test_agent_applies_the_sector_cap_over_the_bus() -> None:
    """PM-NEV-04: sector cap enforced end-to-end over the bus."""
    payload = recommendation_set(recommendation("AAPL"), recommendation("MSFT"))
    bus, graph, sink = wire_pm(
        source_bars=(bar("AAPL", 0, 100.0), bar("MSFT", 0, 100.0)),
        sectors={"AAPL": "Technology", "MSFT": "Technology"},
        settings=PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.05"),
            max_sector_pct=Decimal("0.15"),
            max_names_per_sector=0,
        ),
        portfolio=cash_portfolio(
            "20000.00",
            {"OTHER": 1},
            position_values={"OTHER": Money(amount=Decimal("10000.00"))},
        ),
    )
    graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{payload.run_id}",
        {
            "snapshot": MarketData(
                bars=(*correlated_bars(("AAPL", "MSFT"), days=66), *_flat_bars()),
                quality=DataQualityTrace(requested=3, returned=3),
                provenance=Provenance(run_id=payload.run_id, source_agent="provider"),
            ).model_dump(mode="json")
        },
    )

    result = OrderIntentSet.model_validate(
        bus.request(evaluate_message(payload)).payload
    )

    assert [o.ticker for o in result.approved] == ["AAPL"]
    assert [(r.ticker, r.reason) for r in result.rejected] == [
        ("MSFT", "sector_concentration")
    ]
    assert sink.faults == []


def _flat_bars() -> tuple[OHLCVBar, ...]:
    return tuple(_bar("OTHER", offset, 100.0) for offset in range(66))


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
