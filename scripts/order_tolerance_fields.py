"""Read S149 tolerance evidence off a Fill node.

Agent: tooling
Role: keep the Fill property names the tolerance comparison depends on in one
      place, so the report and its informativeness check cannot disagree.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.order_tolerance_informativeness import ToleranceRow

if TYPE_CHECKING:
    from kernel import Node

_ACTUAL_PRICE_FIELDS = (
    "actual_open_price_cents",
    "broker_price_cents",
    "price_cents",
)


def price_cents(node: Node, field: str) -> int | None:
    """Return an integer cent property, or None when it is absent or typed wrong."""
    value = node.props.get(field)
    return value if isinstance(value, int) else None


def limit_cents(node: Node, mode: str) -> int | None:
    """Return one mode's counterfactual limit price in cents."""
    return price_cents(node, f"order_{mode}_limit_price_cents")


def actual_price_cents(node: Node) -> int | None:
    """Return the price the order actually executed at, by field precedence."""
    for field in _ACTUAL_PRICE_FIELDS:
        value = price_cents(node, field)
        if value is not None:
            return value
    return None


def tolerance_row(node: Node) -> ToleranceRow:
    """Return the applied mode and both candidate bands for one filled order."""
    applied = node.props.get("order_tolerance_mode")
    return ToleranceRow(
        applied_mode=applied if isinstance(applied, str) else None,
        side=str(node.props.get("side", "")),
        flat_limit_cents=limit_cents(node, "flat") or 0,
        scaled_limit_cents=limit_cents(node, "scaled") or 0,
    )
