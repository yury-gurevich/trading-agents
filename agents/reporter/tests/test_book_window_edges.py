"""The book metrics' edges: no exit, the as-of book, removed keys, a read fault (S253).

Agent: reporter
Role: prove what the snapshot reports when the book is thin or cannot be read.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.result import build_snapshot
from agents.reporter.tests.book_fixtures import (
    REPORTED_AT,
    REPORTED_RUN,
    SETTINGS,
    filled,
    pm_run,
    seed_sched_2026_10_01,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

_REMOVED = ("execution_count", "approval_execution_gap", "dropped_decision_count")


def test_no_exit_since_the_inception_omits_the_ratios() -> None:
    """RPT-NEV-03: with no exit carrying P&L, the two ratios are absent, not zero.

    `closed_trades_with_pnl` reads 0.0, as it did before S253.
    """
    graph = InMemoryGraphStore()
    pm_run(graph, REPORTED_RUN, REPORTED_AT)
    filled(graph, "buy:TGT", side="buy", refreshed_at="2026-10-01T22:30:51Z")
    filled(graph, "sell:KO", side="sell", refreshed_at="2026-10-01T22:30:52Z")

    portfolio = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS).portfolio_metrics

    assert portfolio["positions_closed"] == 1.0
    assert portfolio["closed_trades_with_pnl"] == 0.0
    assert "profit_factor" not in portfolio
    assert "expectancy_cents" not in portfolio


def test_positions_held_is_the_as_of_snapshots_holdings() -> None:
    """RPT-OUT-02: the holdings of the latest fresh snapshot at or before the run.

    A snapshot created after the run and a stale one are not read; with none, the
    key is absent.
    """
    graph = InMemoryGraphStore()
    pm_run(graph, REPORTED_RUN, REPORTED_AT)
    _position_snapshot(graph, "before", "2026-10-01T22:35:00Z", 32, status="fresh")
    _position_snapshot(graph, "stale", "2026-10-01T22:36:00Z", 7, status="stale")
    _position_snapshot(graph, "after", "2026-10-01T22:45:00Z", 5, status="fresh")

    portfolio = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS).portfolio_metrics
    assert portfolio["positions_held"] == 32.0

    bare = InMemoryGraphStore()
    pm_run(bare, REPORTED_RUN, REPORTED_AT)
    no_book = build_snapshot(bare, REPORTED_RUN, settings=SETTINGS).portfolio_metrics
    assert "positions_held" not in no_book

    unreadable = InMemoryGraphStore()
    pm_run(unreadable, REPORTED_RUN, REPORTED_AT)
    _position_snapshot(unreadable, "odd", "2026-10-01T22:35:00Z", None, status="fresh")
    odd = build_snapshot(unreadable, REPORTED_RUN, settings=SETTINGS)
    assert "positions_held" not in odd.portfolio_metrics


def test_the_three_removed_keys_are_gone() -> None:
    """RPT-OUT-02: no snapshot carries the keys that described the run's own orders."""
    graph = InMemoryGraphStore()
    seed_sched_2026_10_01(graph)

    snapshot = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS)

    node = graph.get_node("Snapshot", f"snapshot:{REPORTED_RUN}")
    assert node is not None
    written = node.props["metrics"]["portfolio"]
    for key in _REMOVED:
        assert key not in snapshot.portfolio_metrics
        assert key not in written


def test_a_book_read_fault_is_contained() -> None:
    """RPT-NEV-03: a failed Fill read leaves the book keys absent and is a fault.

    The rest of the snapshot is still produced; nothing raises.
    """
    graph = _FillReadFailingGraph()
    seed_sched_2026_10_01(graph)
    sink = CollectingFaultSink()

    snapshot = build_snapshot(graph, REPORTED_RUN, settings=SETTINGS, sink=sink)

    assert "positions_opened" not in snapshot.portfolio_metrics
    assert snapshot.portfolio_metrics["approved_count"] == 4.0
    assert snapshot.headline.summary.startswith("? positions opened; ? closed; ")
    assert [fault.capability for fault in sink.faults] == ["report.book"]


def _position_snapshot(
    graph: InMemoryGraphStore,
    key: str,
    created_at: str,
    holdings: int | None,
    *,
    status: str,
) -> None:
    graph.merge_node(
        "BrokerPositionSnapshot",
        key,
        {
            "status": status,
            "account_status": "fresh",
            "created_at": created_at,
            "account_equity_cents": 10_000_000,
            "holdings": "unreadable"
            if holdings is None
            else [{"market_value_cents": 100_000} for _ in range(holdings)],
        },
    )


class _FillReadFailingGraph(InMemoryGraphStore):
    """In-memory graph whose Fill listing fails."""

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        """Raise for Fill, then behave like the in-memory graph."""
        if label == "Fill":
            raise RuntimeError("Fill read failed")
        return super().list_nodes(label)
