"""Sector name-count concentration tests (PM-NEV-06).

Agent: portfolio_manager
Role: verify the per-sector NAME-COUNT cap rejects a basket of correlated names the
      dollar cap misses, counts already-held positions, and disables at 0.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.common import Money

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import OrderIntent, RejectedOrder

_SECTORS = {"AAPL": "Tech", "MSFT": "Tech", "NVDA": "Tech", "INTC": "Tech"}


def _three_tech_buys(
    max_names_per_sector: int,
    portfolio: PortfolioState | None = None,
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    def rec(ticker: str, confidence: float) -> Recommendation:
        return recommendation(ticker, confidence=confidence).model_copy(
            update={"suggested_stop_pct": 0.05, "suggested_target_pct": 0.10}
        )

    recs = (rec("AAPL", 0.90), rec("MSFT", 0.80), rec("NVDA", 0.70))
    prices = {t: Money(amount=Decimal("100.00")) for t in ("AAPL", "MSFT", "NVDA")}
    return evaluate_recommendations(
        recs,
        prices,
        portfolio or cash_portfolio("10000.00"),
        max_position_pct=Decimal("0.10"),
        max_positions=10,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors=_SECTORS,
        max_sector_pct=Decimal("1"),  # dollar cap disabled — isolate the count cap
        max_names_per_sector=max_names_per_sector,
    )


def test_rejects_third_same_sector_name_over_count_cap() -> None:
    """PM-NEV-06: name-count cap rejects a 3rd correlated name the dollar cap allows."""
    approved, rejected = _three_tech_buys(2)
    assert [o.ticker for o in approved] == ["AAPL", "MSFT"]
    assert [(r.ticker, r.reason) for r in rejected] == [("NVDA", "sector_name_count")]


def test_zero_disables_the_name_count_cap() -> None:
    """PM-NEV-06: max_names_per_sector=0 disables the gate — all approved."""
    approved, rejected = _three_tech_buys(0)
    assert {o.ticker for o in approved} == {"AAPL", "MSFT", "NVDA"}
    assert rejected == ()


def test_held_position_counts_toward_name_cap() -> None:
    """PM-NEV-06: an already-held same-sector name consumes a slot in the count."""
    # BND is held but has no sector classification — it must not seed any count.
    held = cash_portfolio("10000.00", {"INTC": 50, "BND": 10})
    approved, rejected = _three_tech_buys(2, held)
    # INTC already fills 1 of 2 Tech slots, so only AAPL fits; MSFT and NVDA reject.
    assert [o.ticker for o in approved] == ["AAPL"]
    assert [r.reason for r in rejected] == ["sector_name_count", "sector_name_count"]


def test_rebuy_of_held_name_skips_the_count_check() -> None:
    """PM-NEV-06: adding to an already-held name does not consume a new sector slot."""
    held = cash_portfolio("10000.00", {"AAPL": 10})
    approved, rejected = _three_tech_buys(2, held)
    # AAPL re-buy is not a new name, so AAPL+MSFT fill the 2 slots; NVDA rejects.
    assert [o.ticker for o in approved] == ["AAPL", "MSFT"]
    assert [(r.ticker, r.reason) for r in rejected] == [("NVDA", "sector_name_count")]
