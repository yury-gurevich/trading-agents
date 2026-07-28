"""Repair script tests for broker orders missing Fill lineage.

Agent: tooling
Role: verify append-only orphan Fill adoption through execution.write_fills.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from scripts.repair_orphan_fills import repair_graph

from agents.execution.broker import BrokerFill
from contracts.common import Money
from kernel import InMemoryGraphStore

_SINCE = datetime(2026, 7, 20, tzinfo=UTC)


def test_orphan_fill_repair_dry_run_apply_and_second_run() -> None:
    """EXEC-NEV-03 / EXEC-IDM-02: repair converges on the execution Fill key."""
    graph = InMemoryGraphStore()
    _pm_lineage(graph, "pm-run-a", "AMD")
    fill = _fill("pm-run-a:AMD:buy", "AMD", 19, "101.25")

    dry = repair_graph(graph, (fill,), since=_SINCE)
    first = repair_graph(graph, (fill,), apply=True, since=_SINCE)
    node_count = len(graph.list_nodes("Fill"))
    second = repair_graph(graph, (fill,), apply=True, since=_SINCE)

    node = graph.get_node("Fill", "pm-run-a:AMD:buy")
    order = graph.get_node("OrderIntent", "pm-run-a:AMD")
    assert dry.would_record == 1
    assert first.recorded == 1
    assert second.already_recorded == 1
    assert len(graph.list_nodes("Fill")) == node_count
    assert graph.list_nodes("ExecutionRun") == ()
    assert node is not None
    assert order is not None
    assert list(graph.descendants(node, max_depth=1, edge_types={"EXECUTES"})) == [
        order
    ]


def test_repair_adopts_broker_price_not_order_intent_estimate() -> None:
    """EXEC-OUT-02 / EXEC-TYP-01: broker fill price is the repair source."""
    graph = InMemoryGraphStore()
    _pm_lineage(graph, "pm-run-hpe", "HPE", est_price_cents=1)
    fill = _fill("pm-run-hpe:HPE:buy", "HPE", 229, "41.37")

    repair_graph(graph, (fill,), apply=True, since=_SINCE)

    node = graph.get_node("Fill", "pm-run-hpe:HPE:buy")
    assert node is not None
    assert node.props["price_cents"] == 4137


def test_repair_allowlists_probe_orders_with_reason() -> None:
    """EXEC-OBS-01 / EXEC-OBS-02: probe exclusions are explicit data."""
    graph = InMemoryGraphStore()
    fill = _fill("dep-broker-probe-live", "AAPL", 1, "100.00")

    report = repair_graph(graph, (fill,), apply=True, since=_SINCE)

    assert report.ignored == 1
    assert report.rows[0].verdict == "ignored"
    assert "dependency probe" in report.rows[0].reason
    assert graph.list_nodes("Fill") == ()


def test_repair_since_bound_filters_old_orders() -> None:
    """EXEC-OBS-01 / EXEC-OBS-02: repair scan is bounded by submitted_at."""
    graph = InMemoryGraphStore()
    old = _fill(
        "pm-run-old:CSCO:buy", "CSCO", 88, "106.78", submitted_at="2026-07-01T00:00:00Z"
    )

    report = repair_graph(graph, (old,), apply=True, since=_SINCE)

    assert report.rows == ()
    assert graph.list_nodes("Fill") == ()


def _fill(
    key: str,
    ticker: str,
    quantity: int,
    price: str,
    *,
    submitted_at: str = "2026-07-27T13:31:00Z",
) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side="buy",
        quantity=quantity,
        price=Money(amount=Decimal(price)),
        broker_order_id=f"broker:{key}",
        status="filled",
        submitted_at=submitted_at,
    )


def _pm_lineage(
    graph: InMemoryGraphStore,
    pm_run_id: str,
    ticker: str,
    *,
    est_price_cents: int = 10000,
) -> None:
    graph.merge_node("PMRun", pm_run_id, {"status": "complete"})
    graph.merge_node(
        "OrderIntent",
        f"{pm_run_id}:{ticker}",
        {
            "ticker": ticker,
            "action": "buy",
            "quantity": 1,
            "est_price_cents": est_price_cents,
        },
    )
