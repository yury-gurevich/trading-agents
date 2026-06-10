"""Monitor store and position reconstruction tests.

Agent: monitor
Role: verify graph lookup skips and fallback position reconstruction.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.domain.positions import position_from_fill
from agents.monitor.store import fills_for_run
from agents.monitor.tests.helpers import seed_fill
from kernel import InMemoryGraphStore


def test_fills_for_run_ignores_missing_run_sell_orders_and_unfilled_fills() -> None:
    graph = InMemoryGraphStore()

    assert fills_for_run(graph, "missing") == ()

    run = graph.merge_node("PMRun", "pm-run-fixture", {"approved_count": 2})
    sell = graph.merge_node(
        "OrderIntent",
        "pm-run-fixture:MSFT",
        {"ticker": "MSFT", "action": "sell"},
    )
    buy = graph.merge_node(
        "OrderIntent",
        "pm-run-fixture:AAPL",
        {"ticker": "AAPL", "action": "buy"},
    )
    graph.merge_node(
        "Fill",
        "pm-run-fixture:AAPL:buy",
        {"ticker": "AAPL", "status": "rejected"},
    )
    graph.add_edge(sell, run, "EMITTED_BY")
    graph.add_edge(buy, run, "EMITTED_BY")

    assert fills_for_run(graph, "pm-run-fixture") == ()


def test_position_from_fill_uses_fallback_when_order_lineage_is_absent() -> None:
    graph = InMemoryGraphStore()
    seed_fill(graph)
    fill = graph.merge_node(
        "Fill",
        "orphan:AAPL:buy",
        {
            "ticker": "AAPL",
            "quantity": 1,
            "price_cents": 10000,
            "status": "filled",
        },
    )

    draft = position_from_fill(
        graph,
        run_id="orphan",
        fill=fill,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        default_horizon_days=14,
    )

    assert draft.degraded is True
    assert draft.stop_pct == 0.05
    assert draft.target_pct == 0.10
