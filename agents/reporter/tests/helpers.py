"""Reporter test helpers.

Agent: reporter
Role: provide deterministic graph fixtures and message helpers for reporter tests.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from contracts.provider import OHLCVBar
from kernel import AgentMessage, InMemoryGraphStore

RUN_ID = "pm-run-fixture"
TICKER = "AAPL"
POSITION_ID = f"{RUN_ID}:{TICKER}"


def bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    """Build one deterministic OHLCV bar."""
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def seed_full_graph(graph: InMemoryGraphStore, *, include_close: bool = True) -> None:
    """Seed the canonical PM-to-market lineage for reporter unit tests."""
    pm_run = graph.merge_node(
        "PMRun", RUN_ID, {"approved_count": 1, "rejected_count": 1}
    )
    order = graph.merge_node(
        "OrderIntent",
        POSITION_ID,
        _order_props(),
    )
    fill = graph.merge_node(
        "Fill",
        f"{RUN_ID}:{TICKER}:buy",
        {
            "ticker": TICKER,
            "side": "buy",
            "quantity": 3,
            "price_cents": 10100,
            "status": "filled",
        },
    )
    position = graph.merge_node(
        "Position",
        POSITION_ID,
        {
            "run_id": RUN_ID,
            "ticker": TICKER,
            "opened_price_cents": 10100,
            "quantity": 3,
        },
    )
    recommendation = graph.merge_node(
        "Recommendation",
        "analyst-run-fixture:AAPL",
        {"ticker": TICKER, "confidence": 0.82, "technical_score": 0.77},
    )
    candidate = graph.merge_node(
        "Candidate",
        "scan-run-fixture:AAPL",
        {"ticker": TICKER, "rank": 1, "score": 0.91},
    )
    scan = graph.merge_node(
        "ScanRun",
        "scan-run-fixture",
        {"created_at": "2026-06-10T00:00:00+00:00"},
    )
    snapshot = graph.merge_node(
        "MarketSnapshot", "provider-market-fixture", {"bar_count": 6}
    )
    rejection = graph.merge_node(
        "Rejection", f"{RUN_ID}:MSFT", {"ticker": "MSFT", "reason": "risk"}
    )
    graph.add_edge(order, pm_run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(fill, position, "OPENS")
    graph.add_edge(order, recommendation, "APPROVES")
    graph.add_edge(recommendation, candidate, "DERIVED_FROM")
    graph.add_edge(candidate, scan, "SURVIVED")
    graph.add_edge(scan, snapshot, "DERIVED_FROM")
    graph.add_edge(rejection, pm_run, "REJECTED_IN")
    if include_close:
        close = graph.merge_node(
            "CloseDecision",
            f"monitor-run-fixture:{POSITION_ID}:close",
            {
                "ticker": TICKER,
                "position_id": POSITION_ID,
                "decision": "close",
                "trigger": "stop",
                "rationale": "Stop was touched.",
            },
        )
        graph.add_edge(close, position, "CLOSES")


def seed_position_only(graph: InMemoryGraphStore) -> None:
    """Seed a position without lineage to exercise missing-leg handling."""
    graph.merge_node("Position", POSITION_ID, {"ticker": TICKER})


def report_message(run_id: str = RUN_ID) -> AgentMessage:
    """Build a reporter report request."""
    return AgentMessage(
        sender="tester",
        recipient="reporter",
        message_type="request",
        capability="report",
        payload={"run_id": run_id},
    )


def narrative_message(position_id: str = POSITION_ID) -> AgentMessage:
    """Build a reporter narrative request."""
    return AgentMessage(
        sender="tester",
        recipient="reporter",
        message_type="request",
        capability="narrative",
        payload={"position_id": position_id},
    )


def has_edge(
    graph: InMemoryGraphStore,
    parent: tuple[str, str],
    child: tuple[str, str],
    edge_type: str,
) -> bool:
    """Return whether an exact edge is present."""
    return any(
        edge.parent == parent and edge.child == child and edge.edge_type == edge_type
        for edge in graph._edges
    )


def _order_props() -> dict[str, object]:
    return {
        "ticker": TICKER,
        "action": "buy",
        "quantity": 3,
        "est_price_cents": 10100,
        "stop_pct": 0.05,
        "target_pct": 0.10,
    }
