"""Execution run-start broker reconciliation tests.

Agent: execution
Role: prove DL-44 snapshot, divergence Flag, pending-fill refresh, and fail-open.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill, BrokerPosition
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.reconciliation_store import (
    position_divergences,
    write_divergence_flag,
)
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_reconcile_run_start_snapshots_flags_and_refreshes_pending_fills() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    _fill_node(graph, "run:AMD:buy", "filled")
    _fill_node(graph, "run:CSCO:buy", "pending")
    _fill_node(graph, "run:HPE:buy", "pending")
    _fill_node(graph, "run:MRVL:buy", "pending", broker_status="filled")
    _position(graph, "graph:AAPL", "AAPL", 2)
    _position(graph, "graph:MSFT", "MSFT", 1)
    _position(graph, "graph:TSLA", "TSLA", 4)
    _position(graph, "absent:IBM", "IBM", 1, broker_absent=True)
    _position(graph, "s:O", "O", 1, status="closed", broker_superseded_by="b")
    closed = _position(graph, "closed:INTC", "INTC", 1)
    close = graph.merge_node("CloseDecision", "close:INTC", {"decision": "close"})
    graph.add_edge(close, closed, "CLOSES")
    broker = _StaticBroker(
        broker_fills=(
            _fill("run:CSCO:buy", "CSCO", "filled", Decimal("66.66")),
            _fill("run:HPE:buy", "HPE", "pending", Decimal("20.00")),
            _fill("external:NVDA:buy", "NVDA", "rejected", Decimal("1.00")),
        ),
        broker_positions=(
            BrokerPosition("AAPL", 2, 10000, 20000),
            BrokerPosition("NVDA", 3, 90000, 270000),
            BrokerPosition("TSLA", 5, 25000, 125000),
        ),
    )
    _fill_node(graph, "external:NVDA:buy", "pending", broker_order_id="paper:external")

    snapshot = reconcile_run_start(graph, broker, sink, run_id="pm-run")
    assert snapshot is not None
    write_divergence_flag(
        graph,
        snapshot=snapshot,
        divergences=("extra_graph_position MSFT graph_qty=1",),
    )

    refreshed = graph.get_node("Fill", "run:CSCO:buy")
    rejected = graph.get_node("Fill", "external:NVDA:buy")
    hpe = graph.get_node("Fill", "run:HPE:buy")
    mrvl = graph.get_node("Fill", "run:MRVL:buy")
    flag = graph.list_nodes("Flag")[0]
    assert refreshed is not None
    assert hpe is not None
    assert mrvl is not None
    assert refreshed.props["status"] == "pending"
    assert refreshed.props["broker_status"] == "filled"
    assert refreshed.props["broker_price_cents"] == 6666
    assert rejected is not None
    assert rejected.props["broker_status"] == "rejected"
    assert "broker_price_cents" not in rejected.props
    assert hpe.props.get("broker_status") is None
    assert mrvl.props["broker_status"] == "filled"
    assert snapshot.props["status"] == "fresh"
    assert snapshot.props["holding_count"] == 3
    assert "missing_graph_position NVDA broker_qty=3" in flag.props["reason"]
    assert "extra_graph_position MSFT graph_qty=1" in flag.props["reason"]
    assert "qty_mismatch TSLA graph_qty=4 broker_qty=5" in flag.props["reason"]


def test_reconcile_run_start_writes_stale_snapshot_on_broker_read_error() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    node = reconcile_run_start(graph, _FailingBroker(), sink, run_id="pm-run")

    assert node is not None
    assert node.props["status"] == "stale"
    assert node.props["holding_count"] == 0
    assert "broker positions read failed" in node.props["stale_reason"]
    assert len(sink.faults) == 2
    assert graph.list_nodes("Flag") == ()


def test_position_divergences_is_empty_when_books_match() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "broker:AAPL:2:10000", "AAPL", 2)
    assert position_divergences(graph, (BrokerPosition("AAPL", 2, 10000, 20000),)) == ()


@dataclass
class _StaticBroker:
    broker_fills: tuple[BrokerFill, ...]
    broker_positions: tuple[BrokerPosition, ...]

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
    ) -> BrokerFill:
        raise AssertionError("reconciliation must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        return self.broker_fills

    def positions(self) -> tuple[BrokerPosition, ...]:
        return self.broker_positions


class _FailingBroker:
    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
    ) -> BrokerFill:
        raise AssertionError("reconciliation must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        raise RuntimeError("offline")

    def positions(self) -> tuple[BrokerPosition, ...]:
        raise RuntimeError("offline")


def _fill(
    key: str,
    ticker: str,
    status: Literal["filled", "partial", "rejected", "pending"],
    price: Decimal,
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side="buy",
        quantity=1,
        price=Money(amount=price),
        broker_order_id=f"paper:{key}",
        status=status,
    )


def _fill_node(
    graph: InMemoryGraphStore,
    key: str,
    status: str,
    *,
    broker_order_id: str | None = None,
    broker_status: str | None = None,
) -> None:
    props: dict[str, object] = {
        "ticker": key.split(":")[1],
        "side": "buy",
        "quantity": 1,
        "price_cents": 10000,
        "price_currency": "USD",
        "broker_order_id": broker_order_id or f"paper:{key}",
        "status": status,
        "reason": None,
    }
    if broker_status is not None:
        props["broker_status"] = broker_status
    graph.merge_node("Fill", key, props)


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **extra: object,
) -> Node:
    props = {
        "ticker": ticker,
        "quantity": quantity,
        "opened_price_cents": 10000,
        "status": "open",
        **extra,
    }
    return graph.merge_node("Position", key, props)
