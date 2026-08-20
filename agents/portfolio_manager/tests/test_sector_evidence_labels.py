"""Sector concentration evidence-label tests.

Agent: portfolio_manager
Role: verify sector gate reports name units and scopes without changing gates.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.concentration import SectorBook
from agents.portfolio_manager.domain.position_gates import sector_rejection
from agents.portfolio_manager.tests.helpers import recommendation

if TYPE_CHECKING:
    from contracts.portfolio_manager import RejectedOrder


def test_sector_rejection_maps_each_failing_outcome_to_its_reason() -> None:
    """PM-OUT-03: the book reports outcomes; `sector_rejection` names the reason.

    Was `SectorBook.rejection`, a second copy of this mapping that only tests ever
    called (DL-97). Exercising the live function over `book.outcomes(...)` tests the
    composition the PM actually runs.
    """
    book = SectorBook({"AAPL": "Tech", "MSFT": "Tech"}, ("AAPL",))
    item = recommendation("MSFT")

    def _reject(cost: str, pct: str, names: int) -> RejectedOrder | None:
        outcomes = book.outcomes(
            item,
            Decimal(cost),
            Decimal("1000.00"),
            max_sector_pct=Decimal(pct),
            max_names_per_sector=names,
        )
        return sector_rejection(item.ticker, outcomes, ())

    name_count = _reject("100.00", "1", 1)
    sector_cap = _reject("400.00", "0.30", 3)
    ok = _reject("100.00", "0.30", 3)
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


def test_sector_deployment_detail_names_batch_scope_and_unit() -> None:
    """PM-OBS-01: sector deployment evidence names batch scope and USD unit."""
    book = SectorBook(
        {"AMD": "Semiconductors", "NVDA": "Semiconductors", "AVGO": "Semiconductors"},
        ("AMD", "NVDA"),
    )

    outcomes = book.outcomes(
        recommendation("AVGO"),
        Decimal("786.04"),
        Decimal("102777.00"),
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )

    assert len(outcomes) == 2
    sector_pct, sector_names = outcomes[0], outcomes[1]

    assert sector_pct.passed is True
    assert "deployed_this_batch_usd=0.00" in sector_pct.detail
    assert "deployed=" not in sector_pct.detail
    assert "order_cost_usd=786.04" in sector_pct.detail
    assert "portfolio_value_usd=102777.00" in sector_pct.detail
    assert "existing_sector_issuers=2" in sector_names.detail
