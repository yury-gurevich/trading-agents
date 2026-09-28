"""Portfolio Manager held-book test helpers (S240).

Agent: portfolio_manager
Role: build run snapshots with marks, adopted Position nodes and resume lineage.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node


def book_snapshot(
    graph: InMemoryGraphStore,
    run_id: str,
    marks: dict[str, int],
    *,
    equity_cents: int = 10_000_000,
    status: str = "fresh",
) -> None:
    """Write one execution-shaped snapshot listing ``marks`` (ticker -> cents)."""
    props: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "created_at": "2026-09-25T13:25:00+00:00",
        "holding_count": len(marks),
        "holdings": [
            {"ticker": ticker, "market_value_cents": cents}
            for ticker, cents in marks.items()
        ],
        "account_status": status,
    }
    if status == "fresh":
        props.update(
            {
                "account_cash_cents": equity_cents,
                "account_equity_cents": equity_cents,
                "account_buying_power_cents": equity_cents,
            }
        )
    else:
        props["account_stale_reason"] = "broker account read failed: RuntimeError"
    graph.merge_node("BrokerPositionSnapshot", f"snapshot:{run_id}", props)


def held(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    *,
    cost_cents: int,
    adoption_cents: int | None = None,
) -> None:
    """Write one open Position; ``adoption_cents`` is the adoption-day mark."""
    props: dict[str, object] = {
        "ticker": ticker,
        "quantity": quantity,
        "opened_price_cents": cost_cents,
        "status": "open",
    }
    if adoption_cents is not None:
        props["broker_market_value_cents"] = adoption_cents
    graph.merge_node("Position", key, props)


def resumed_request(
    graph: InMemoryGraphStore, child_id: str, source_run_id: str
) -> None:
    """Write a child RunRequest carrying the props the resume writes."""
    graph.merge_node(
        "RunRequest",
        f"run-request:{child_id}",
        {"run_id": child_id, "source_run_id": source_run_id, "resume_from": "pm"},
    )


class CountingGraph(InMemoryGraphStore):
    """A graph that refuses to answer more than ``limit`` keyed reads."""

    def __init__(self, limit: int) -> None:
        """Start counting keyed reads from zero."""
        super().__init__()
        self.limit = limit
        self.reads = 0

    def get_node(self, label: str, key: str) -> Node | None:
        """Count the read; fail loud past the limit instead of looping forever."""
        self.reads += 1
        if self.reads > self.limit:
            raise AssertionError(f"unbounded walk: {self.reads} keyed reads")
        return super().get_node(label, key)
