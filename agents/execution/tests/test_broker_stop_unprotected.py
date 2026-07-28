"""Execution broker-stop unprotected-position tests.

Agent: execution
Role: prove broker-stop retries and fallback thresholds are visible.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.execution.broker_stops import place_broker_stops
from agents.execution.fill_attempts import fill_attempt_chain
from agents.execution.tests.broker_stop_helpers import (
    PendingStopBroker,
    RuntimeStopBroker,
    order_set,
)
from contracts.positions import open_positions
from contracts.stop_rule import check_stop
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from contracts.common import Money


class _ForbiddenStopBroker(RuntimeStopBroker):
    def __init__(self) -> None:
        super().__init__()
        self.submitted: list[str] = []

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        del ticker, side, quantity, stop_price, tif
        self.submitted.append(idempotency_key)
        raise RuntimeError("HTTP Error 403: Forbidden")


def test_broker_reconciled_abt_shape_reaches_stop_submission() -> None:
    """EXEC-FAIL-01 / EXEC-OBS-02: refused stops are loud, not silent skips."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = _ForbiddenStopBroker()
    _position(
        graph,
        "broker:ABT:96:10437",
        "ABT",
        96,
        opened_price_cents=10437,
        stop_pct=0.05,
        provenance="reconciled-from-broker",
        degraded=True,
    )
    ref = open_positions(graph)[0].position_ref

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "ABT", "quantity": 96},)),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == [f"stop:{ref}:ABT"]
    assert graph.list_nodes("BrokerStopOrder") == ()
    assert sink.faults[-1].error_type == "UnprotectedPosition"
    assert "ABT" in sink.faults[-1].message


def test_missing_position_stop_pct_uses_visible_execution_fallback() -> None:
    """EXEC-DEP-03 / EXEC-OBS-02: fallback stop policy is explicit and auditable."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    _position(graph, "broker:ABT:96:10437", "ABT", 96, opened_price_cents=10437)
    ref = open_positions(graph)[0].position_ref

    place_broker_stops(
        graph,
        broker,
        CollectingFaultSink(),
        order_set("pm-run"),
        _snapshot(graph, ({"ticker": "ABT", "quantity": 96},)),
        fallback_stop_pct=0.05,
    )

    stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:ABT")
    fill = graph.get_node("Fill", f"stop:{ref}:ABT")
    assert stop is not None
    assert fill is not None
    assert stop.props["stop_price_cents"] == 9915
    assert check_stop(9915, 10437, 0.05)
    assert not check_stop(9916, 10437, 0.05)
    assert stop.props["stop_pct_source"] == "fallback"
    assert fill.props["stop_pct_source"] == "fallback"


def test_refused_stop_retries_with_same_broker_key_and_new_fill_attempt() -> None:
    """EXEC-IDM-02 / EXEC-OBS-02: retry keeps broker key and appends evidence."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = _ForbiddenStopBroker()
    _position(graph, "broker:ABT:96:10437", "ABT", 96, opened_price_cents=10437)
    ref = open_positions(graph)[0].position_ref
    snapshot = _snapshot(graph, ({"ticker": "ABT", "quantity": 96},))

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        snapshot,
        fallback_stop_pct=0.05,
    )
    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run"),
        snapshot,
        fallback_stop_pct=0.05,
    )

    key = f"stop:{ref}:ABT"
    chain = fill_attempt_chain(graph, key)
    assert broker.submitted == [key, key]
    assert [node.key for node in chain] == [key, f"{key}#1"]
    assert {node.props["broker_idempotency_key"] for node in chain} == {key}
    assert [fault.error_type for fault in sink.faults].count("UnprotectedPosition") == 2


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    **props: object,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
            **props,
        },
    )


def _snapshot(graph: InMemoryGraphStore, holdings: tuple[object, ...]) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": holdings},
    )
