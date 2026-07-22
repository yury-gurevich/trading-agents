"""Sector-concentration cap tests.

Agent: portfolio_manager
Role: verify the per-sector deployment cap rejects over-concentrated orders, skips
      unknown sectors, and disables at 1.0 — as a unit and over the bus.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.concentration import SectorBook
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
from contracts.common import Money
from contracts.portfolio_manager import OrderIntentSet

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
        cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
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


def test_unknown_sector_is_not_capped() -> None:
    # MSFT has no sector, so the cap is skipped for it even under a tight cap.
    approved, _rejected = _two_tech_buys({"AAPL": "Tech"}, Decimal("0.15"))
    assert {o.ticker for o in approved} == {"AAPL", "MSFT"}


def test_max_sector_pct_of_one_disables_the_cap() -> None:
    approved, rejected = _two_tech_buys({"AAPL": "Tech", "MSFT": "Tech"}, Decimal("1"))
    assert {o.ticker for o in approved} == {"AAPL", "MSFT"}
    assert rejected == ()


def test_sector_book_rejection_uses_explicit_outcomes() -> None:
    book = SectorBook({"AAPL": "Tech", "MSFT": "Tech"}, ("AAPL",))
    item = recommendation("MSFT")

    name_count = book.rejection(
        item,
        Decimal("100.00"),
        Decimal("1000.00"),
        max_sector_pct=Decimal("1"),
        max_names_per_sector=1,
    )
    sector_cap = book.rejection(
        item,
        Decimal("400.00"),
        Decimal("1000.00"),
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )
    ok = book.rejection(
        item,
        Decimal("100.00"),
        Decimal("1000.00"),
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )
    zero_value = book.outcomes(
        item,
        Decimal("100.00"),
        Decimal("0"),
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    assert name_count is not None
    assert name_count.reason == "sector_name_count"
    assert sector_cap is not None
    assert sector_cap.reason == "sector_concentration"
    assert ok is None
    assert zero_value[0].value == 0.0


def test_sector_book_holds_dollar_cap_boundary() -> None:
    """Kills
    agents.portfolio_manager.domain.concentration.xǁSectorBookǁoutcomes__mutmut_11.
    """
    book = SectorBook({"AAPL": "Tech"}, ())
    item = recommendation("AAPL")
    observed = []
    for cost in (Decimal("299.00"), Decimal("300.00"), Decimal("301.00")):
        outcome = book.outcomes(
            item,
            cost,
            Decimal("1000.00"),
            max_sector_pct=Decimal("0.30"),
            max_names_per_sector=0,
        )[0]
        observed.append((round(outcome.value, 3), outcome.threshold, outcome.passed))

    assert observed == [(0.299, 0.3, True), (0.3, 0.3, True), (0.301, 0.3, False)]


def test_agent_applies_the_sector_cap_over_the_bus() -> None:
    """PM-NEV-04: sector cap enforced end-to-end over the bus."""
    payload = recommendation_set(recommendation("AAPL"), recommendation("MSFT"))
    bus, _graph, sink = wire_pm(
        source_bars=(bar("AAPL", 0, 100.0), bar("MSFT", 0, 100.0)),
        sectors={"AAPL": "Technology", "MSFT": "Technology"},
        settings=PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.10"),
            max_sector_pct=Decimal("0.15"),
        ),
    )

    result = OrderIntentSet.model_validate(
        bus.request(evaluate_message(payload)).payload
    )

    assert [o.ticker for o in result.approved] == ["AAPL"]
    assert [(r.ticker, r.reason) for r in result.rejected] == [
        ("MSFT", "sector_concentration")
    ]
    assert sink.faults == []
