"""Execution Fill attempt-chain tests.

Agent: execution
Role: prove broker idempotency keys remain queryable across immutable attempts.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill
from agents.execution.fill_attempts import (
    attempt_ordinal,
    broker_idempotency_key,
    fill_attempt_chain,
    latest_fill_attempt,
)
from agents.execution.store import write_fills
from contracts.common import Money
from kernel import InMemoryGraphStore


def test_write_fills_appends_conflicting_exit_attempt_without_rewrite() -> None:
    """DL-70 / S145 item 1: planted price drift writes attempt #1, not a rewrite."""
    graph = InMemoryGraphStore()
    key = "exit:position-1:MRVL:sell"
    first = _broker_fill(key, ticker="MRVL", side="sell", price="194.51")
    replay = _broker_fill(
        key, ticker="MRVL", side="sell", price="189.28", status="rejected"
    )

    write_fills(graph, run_id="execution-submit-first", fills=(first,))
    write_fills(graph, run_id="execution-submit-replay", fills=(replay,))

    original = graph.get_node("Fill", key)
    attempt = graph.get_node("Fill", f"{key}#1")
    assert original is not None
    assert attempt is not None
    assert original.props["price_cents"] == 19451
    assert original.props["status"] == "filled"
    assert attempt.props["price_cents"] == 18928
    assert attempt.props["status"] == "rejected"
    assert attempt.props["broker_idempotency_key"] == key
    assert attempt.props["attempt_ordinal"] == 1


def test_fill_attempt_chain_recovers_legacy_suffixes_and_stamped_props() -> None:
    """S145 item 1: old Fill keys and new attempt props stay in one chain."""
    graph = InMemoryGraphStore()
    key = "exit:position-2:MRVL:sell"
    base = graph.merge_node("Fill", key, {"ticker": "MRVL"})
    stamped = graph.merge_node(
        "Fill",
        f"{key}#1",
        {"broker_idempotency_key": key, "attempt_ordinal": 1},
    )
    suffixed = graph.merge_node("Fill", f"{key}#2", {"ticker": "MRVL"})

    chain = fill_attempt_chain(graph, key)

    assert chain == (base, stamped, suffixed)
    assert latest_fill_attempt(graph, key) == suffixed
    assert [attempt_ordinal(node, key) for node in chain] == [0, 1, 2]
    assert broker_idempotency_key(stamped) == key
    assert broker_idempotency_key(suffixed) == key


def _broker_fill(
    key: str,
    *,
    ticker: str,
    side: Literal["buy", "sell"],
    price: str,
    status: Literal["filled", "partial", "rejected", "pending"] = "filled",
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side=side,
        quantity=1,
        price=Money(amount=Decimal(price)),
        broker_order_id=f"paper:{key}",
        status=status,
    )
