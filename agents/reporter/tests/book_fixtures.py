"""The S253 book-window fixture: sched-2026-10-01, rebuilt synthetic.

Agent: reporter
Role: seed PM runs and broker Fills whose refresh times place them in run windows.
External I/O: none.

The reported run's own four buys sit in its lineage with no `broker_status`: the
orders are submitted for the next open and have not filled when it is reported.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from agents.reporter.settings import ReporterSettings

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore, Node

PREVIOUS_RUN = "sched-2026-09-30"
REPORTED_RUN = "sched-2026-10-01"
PREVIOUS_AT = "2026-10-01T03:57:58+00:00"
REPORTED_AT = "2026-10-01T22:40:17+00:00"
SETTINGS = ReporterSettings(performance_inception=date(2026, 8, 10))


def pm_run(graph: InMemoryGraphStore, run_id: str, created_at: str | None) -> Node:
    """Write one PMRun, with `created_at` only when one is given."""
    props: dict[str, object] = {"approved_count": 4, "rejected_count": 0}
    if created_at is not None:
        props["created_at"] = created_at
    return graph.merge_node("PMRun", run_id, props)


def filled(
    graph: InMemoryGraphStore,
    key: str,
    *,
    side: str,
    refreshed_at: str,
    pnl_cents: int | None = None,
    stop: bool = False,
) -> Node:
    """Write one Fill the broker filled, as execution leaves it (`status` pending)."""
    ticker = key.split(":")[-1]
    props: dict[str, object] = {
        "ticker": ticker,
        "side": side,
        "quantity": 1,
        "status": "pending",
        "broker_status": "filled",
        "broker_status_refreshed_at": refreshed_at,
    }
    if pnl_cents is not None:
        props["realized_pnl_cents"] = pnl_cents
    if stop:
        props["stop_order_key"] = f"stop:{ticker}"
    return graph.merge_node("Fill", key, props)


def own_unfilled_buy(graph: InMemoryGraphStore, run: Node, ticker: str) -> None:
    """Write one of the run's own buys in its lineage, submitted and not filled."""
    order = graph.merge_node(
        "OrderIntent", f"{run.key}:{ticker}", {"ticker": ticker, "action": "buy"}
    )
    fill = graph.merge_node(
        "Fill",
        f"{run.key}:{ticker}:buy",
        {
            "ticker": ticker,
            "side": "buy",
            "quantity": 1,
            "status": "pending",
            "submitted_at": "2026-10-01T22:51:00+00:00",
        },
    )
    position = graph.merge_node(
        "Position", f"{run.key}:{ticker}", {"run_id": run.key, "ticker": ticker}
    )
    graph.add_edge(order, run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(fill, position, "OPENS")


def seed_sched_2026_10_01(graph: InMemoryGraphStore) -> None:
    """Seed the spec's fixture: the run, the one before it, and their fills."""
    pm_run(graph, PREVIOUS_RUN, PREVIOUS_AT)
    reported = pm_run(graph, REPORTED_RUN, REPORTED_AT)
    filled(graph, "buy:TGT", side="buy", refreshed_at="2026-10-01T22:30:51+00:00")
    filled(
        graph,
        "stop:JNJ",
        side="sell",
        refreshed_at="2026-10-01T22:30:52+00:00",
        pnl_cents=-2_892,
        stop=True,
    )
    filled(
        graph,
        "stop:C",
        side="sell",
        refreshed_at="2026-10-01T22:30:52+00:00",
        pnl_cents=-4_627,
        stop=True,
    )
    filled(
        graph,
        "stop:DE",
        side="sell",
        refreshed_at="2026-10-01T22:30:53+00:00",
        pnl_cents=-3_186,
        stop=True,
    )
    for ticker in ("JNJ", "C", "EMR", "DE"):
        own_unfilled_buy(graph, reported, ticker)
    filled(
        graph,
        "older-stop:MRK",
        side="sell",
        refreshed_at="2026-09-30T22:30:50+00:00",
        pnl_cents=-3_824,
        stop=True,
    )
    filled(
        graph,
        "pre-inception:XOM",
        side="sell",
        refreshed_at="2026-08-07T20:00:00+00:00",
        pnl_cents=90_000,
    )
