"""Execution domain and store edge-case tests.

Agent: execution
Role: cover broker-order mapping, reconciliation discrepancies, and lineage skips.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import cast

import pytest

from agents.execution.broker import BrokerFill
from agents.execution.domain.orders import order_from_intent
from agents.execution.domain.reconcile import reconcile_fills
from agents.execution.store import write_fills
from agents.execution.tests.helpers import order_set
from contracts.common import Action, Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent
from kernel import InMemoryGraphStore


def test_order_from_intent_supports_sell_and_rejects_hold() -> None:
    sell = _intent("AAPL", "sell")
    hold = _intent("MSFT", "hold")
    payload = order_set(sell, hold)

    order = order_from_intent(payload, sell)

    assert order.idempotency_key == "pm-run-fixture:AAPL:sell"
    assert order.side == "sell"
    with pytest.raises(ValueError, match="only buy or sell"):
        order_from_intent(payload, hold)


def test_order_from_intent_uses_position_ref_for_exit_only() -> None:
    buy = _intent("AAPL", "buy")
    sell = _intent("LOW", "sell").model_copy(update={"position_ref": "abc123"})
    payload = order_set(buy, sell)

    buy_order = order_from_intent(payload, buy)
    sell_order = order_from_intent(payload, sell)

    assert buy.position_ref is None
    assert buy_order.idempotency_key == "pm-run-fixture:AAPL:buy"
    assert sell_order.idempotency_key == "exit:abc123:LOW:sell"


def test_reconcile_reports_missing_and_mismatched_broker_fills() -> None:
    fill = _broker_fill("pm-run:AAPL:buy")

    matched = reconcile_fills((fill,), (fill,))
    missing = reconcile_fills((fill,), ())
    mismatch = reconcile_fills((fill,), (replace(fill, status="pending"),))

    assert matched == (1, ())
    assert missing == (0, ("pm-run:AAPL:buy: missing_broker_fill",))
    assert mismatch == (0, ("pm-run:AAPL:buy: broker_mismatch",))


def test_write_fills_skips_absent_or_non_pm_order_lineage() -> None:
    graph = InMemoryGraphStore()
    payload = order_set(_intent("AAPL", "buy"))
    bad_payload = payload.model_copy(
        update={
            "provenance": Provenance(
                run_id=payload.run_id,
                source_agent="portfolio_manager",
                graph_node_id="Other:pm-run-fixture",
            )
        }
    )

    write_fills(graph, run_id="execution-submit-1", fills=(_broker_fill("one"),))
    write_fills(
        graph,
        run_id="execution-submit-2",
        fills=(_broker_fill("two"),),
        order_set=payload,
    )
    write_fills(
        graph,
        run_id="execution-submit-3",
        fills=(_broker_fill("three"),),
        order_set=bad_payload,
    )

    assert graph.get_node("Fill", "one") is not None
    assert graph.get_node("Fill", "two") is not None
    assert graph.get_node("Fill", "three") is not None
    fill = graph.get_node("Fill", "two")
    assert fill is not None
    assert list(graph.descendants(fill, max_depth=1)) == []


def _intent(ticker: str, action: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action=cast("Action", action),
        quantity=1,
        est_price=Money(amount=Decimal("10.00")),
        rationale=Explanation(summary="fixture order"),
    )


def _broker_fill(key: str) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker="AAPL",
        side="buy",
        quantity=1,
        price=Money(amount=Decimal("10.00")),
        broker_order_id=f"paper:{key}",
        status="filled",
    )
