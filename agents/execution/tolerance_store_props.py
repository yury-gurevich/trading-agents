"""Execution Fill tolerance evidence serialization.

Agent: execution
Role: convert resolved order tolerance evidence into Fill graph properties.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from contracts.common import Money

CENTS_PER_DOLLAR = Decimal("100")


def order_tolerance_props(fill: BrokerFill) -> dict[str, object]:
    """Return S149 Fill properties when tolerance evidence is attached."""
    props: dict[str, object] = {}
    if fill.order_tolerance_mode is None:
        return props
    props["order_tolerance_mode"] = fill.order_tolerance_mode
    if fill.order_counterfactual_mode is not None:
        props["order_counterfactual_mode"] = fill.order_counterfactual_mode
    _add_money_props(props, "order_decided_price", fill.order_decided_price)
    props["order_applied_tolerance_bps"] = fill.order_applied_tolerance_bps
    _add_money_props(props, "order_applied_limit_price", fill.order_applied_limit_price)
    props["order_counterfactual_tolerance_bps"] = (
        fill.order_counterfactual_tolerance_bps
    )
    _add_money_props(
        props,
        "order_counterfactual_limit_price",
        fill.order_counterfactual_limit_price,
    )
    props["order_flat_tolerance_bps"] = fill.order_flat_tolerance_bps
    _add_money_props(props, "order_flat_limit_price", fill.order_flat_limit_price)
    props["order_scaled_tolerance_bps"] = fill.order_scaled_tolerance_bps
    _add_money_props(props, "order_scaled_limit_price", fill.order_scaled_limit_price)
    if fill.order_decision_atr_pct is not None:
        props["order_decision_atr_pct"] = fill.order_decision_atr_pct
    props["order_volatility_present"] = fill.order_volatility_present
    props["order_volatility_fallback"] = fill.order_volatility_fallback
    return props


def _add_money_props(
    props: dict[str, object], prefix: str, money: Money | None
) -> None:
    if money is None:
        return
    props[f"{prefix}_cents"] = _money_to_cents(money)
    props[f"{prefix}_currency"] = money.currency


def _money_to_cents(money: Money) -> int:
    cents = (money.amount * CENTS_PER_DOLLAR).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)
