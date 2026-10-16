"""Broker quantity and ended-order mapping proofs.

Agent: execution
Role: prove an ended partial order preserves ordered and executed sizes.
External I/O: none.
"""

from decimal import Decimal
from typing import Literal

import pytest

from agents.execution import alpaca_orders
from agents.execution.broker import BrokerFill, executed_quantity
from agents.execution.tests.partial_fill_helpers import mapped_unh, unh_order
from contracts.common import Money


def test_an_expired_order_that_filled_part_is_a_fill_of_that_part() -> None:
    """EXEC-OUT-07 / EXEC-TYP-04: the filled share survives the expired rest."""
    fill = mapped_unh()
    assert fill.status == "filled"
    assert fill.quantity == 2
    assert fill.filled_quantity == 1
    assert executed_quantity(fill) == 1
    assert fill.price.amount == Decimal("401.11")
    assert fill.order_status == "expired"
    assert fill.reason is None


@pytest.mark.parametrize("status", ["expired", "canceled", "cancelled"])
def test_every_ended_status_with_a_fill_is_filled(status: str) -> None:
    """EXEC-OUT-07: each supported ended status keeps its executed share."""
    fill = mapped_unh(status=status)
    assert fill.status == "filled"
    assert fill.filled_quantity == 1
    assert fill.order_status == status
    assert fill.reason is None


@pytest.mark.parametrize("filled_qty", ["0", None])
def test_an_ended_order_with_nothing_filled_stays_unfilled(
    filled_qty: str | None,
) -> None:
    """EXEC-OUT-07: an ended zero-fill order remains rejected and unexecuted."""
    fill = mapped_unh(filled_qty=filled_qty)
    assert fill.status == "rejected"
    assert fill.reason == "expired"
    assert executed_quantity(fill) == 0


def test_a_partly_filled_order_in_flight_stays_partial() -> None:
    """EXEC-STA-05: a working partial order keeps refreshing until it ends."""
    fill = mapped_unh(status="partially_filled")
    assert fill.status == "partial"
    assert fill.filled_quantity == 1
    assert executed_quantity(fill) == 1


def test_a_replaced_order_is_not_read_as_a_fill() -> None:
    """EXEC-OUT-07: replaced orders stay outside the ended-partial rule."""
    fill = mapped_unh(status="replaced")
    assert fill.status == "rejected"
    assert fill.reason == "replaced"


def test_a_fractional_or_missing_filled_qty_is_read_as_whole_shares() -> None:
    """EXEC-TYP-04: decimal-text shares parse and absent quantities stay absent."""
    fill = mapped_unh(filled_qty="1.0")
    assert fill.filled_quantity == 1
    assert alpaca_orders.filled_quantity_of(unh_order(filled_qty="")) is None
    order = unh_order()
    del order["filled_qty"]
    assert alpaca_orders.filled_quantity_of(order) is None


@pytest.mark.parametrize(
    ("status", "expected"),
    [("filled", 3), ("partial", 3), ("rejected", 0), ("pending", 0)],
)
def test_where_the_broker_does_not_say_the_order_quantity_stands(
    status: Literal["filled", "partial", "rejected", "pending"], expected: int
) -> None:
    """EXEC-TYP-04: legacy brokers fall back only for executed outcomes."""
    fill = BrokerFill(
        "legacy", "UNH", "buy", 3, Money(amount=Decimal("401.11")), "id", status
    )
    assert fill.filled_quantity is None
    assert executed_quantity(fill) == expected
