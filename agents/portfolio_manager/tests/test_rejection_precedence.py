"""Portfolio Manager rejection-precedence tests.

Agent: portfolio_manager
Role: pin which gate a rejection names when several would fail, so the order the
      stages are evaluated in cannot be changed silently by a refactor.
External I/O: none.

Found while splitting `risk.py` (2026-08-08): reordering the sizing and reward-risk
stages passed all 86 existing PM tests. Every reason string the operator reads on a
`SKIP` line depends on that order — S161/S162 exist because `max_positions` shadows
`cash_available` — so the precedence needs its own guard.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.tests.helpers import cash_portfolio, recommendation
from contracts.common import Money

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.portfolio_manager import OrderIntent, RejectedOrder

_PRICE = {"AAPL": Money(amount=Decimal("100.00"))}


def _evaluate(
    portfolio: PortfolioState, **overrides: Any
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    kwargs: dict[str, Any] = {
        "max_position_pct": Decimal("0.10"),
        "max_positions": 10,
        "cash_buffer_pct": Decimal("0"),
        "min_order_quantity": 1,
        "default_stop_pct": 0.05,
        "default_target_pct": 0.10,
        "min_reward_risk_ratio": 1.5,
    }
    kwargs.update(overrides)
    return evaluate_recommendations(
        (recommendation("AAPL"),), _PRICE, portfolio, **kwargs
    )


def test_sizing_gates_are_named_before_reward_risk() -> None:
    """PM-OUT-03 / PM-OBS-01: a name-count failure outranks a reward-risk failure.

    `min_reward_risk_ratio=99.0` makes reward-risk fail for any stop/target, and the
    book is already full, so both stages would reject. The reason must stay the
    sizing one.
    """
    portfolio = cash_portfolio("100000", {f"HELD{i}": 1 for i in range(10)})

    approved, rejected = _evaluate(
        portfolio, max_positions=10, min_reward_risk_ratio=99.0
    )

    assert approved == ()
    assert rejected[0].reason == "max_positions"


def test_reward_risk_is_named_before_the_sector_cap() -> None:
    """PM-OUT-03 / PM-OBS-01: reward-risk outranks a sector-concentration failure.

    The order passes every sizing gate, so only the reward-risk and sector stages
    can reject it, and reward-risk is evaluated first.
    """
    portfolio = cash_portfolio("100000")

    approved, rejected = _evaluate(
        portfolio,
        min_reward_risk_ratio=99.0,
        sectors={"AAPL": "tech"},
        max_sector_pct=Decimal("0"),
        max_names_per_sector=0,
    )

    assert approved == ()
    assert rejected[0].reason == "reward_risk_below_min"


def test_a_rejection_names_one_gate_but_reports_every_gate_evaluated() -> None:
    """PM-OBS-01: the losing stage owns the reason; the evidence stays additive."""
    portfolio = cash_portfolio("100000", {f"HELD{i}": 1 for i in range(10)})

    _, rejected = _evaluate(portfolio, max_positions=10, min_reward_risk_ratio=99.0)

    names = tuple(outcome.name for outcome in rejected[0].gate_report)
    assert names == ("sizing", "min_order_quantity", "max_positions", "cash_available")
    assert "reward_risk" not in names
