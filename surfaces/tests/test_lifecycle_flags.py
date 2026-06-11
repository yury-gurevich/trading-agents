"""Lifecycle and flag surface query tests.

Agent: surfaces
Role: verify position lifecycle and pending-flag projections.
External I/O: none.
"""

from __future__ import annotations

from typing import cast

from kernel import InMemoryGraphStore, Node
from surfaces.queries import (
    all_position_lifecycles,
    pending_flags,
    position_lifecycle,
)


def test_position_lifecycle_returns_full_entry_exit_story() -> None:
    graph = InMemoryGraphStore()
    _seed_full_lifecycle(graph)

    lifecycle = position_lifecycle(graph, "pm-run:AAPL")

    assert lifecycle is not None
    assert lifecycle.ticker == "AAPL"
    assert lifecycle.quantity == 3
    assert lifecycle.opened_price_cents == 10100
    assert lifecycle.status == "closed"
    assert lifecycle.close_trigger == "stop"
    assert lifecycle.run_id == "pm-run"
    assert lifecycle.recommendation_confidence == 0.82
    assert lifecycle.narrative_text == "AAPL closed on stop."


def test_position_lifecycle_handles_open_orphan_and_missing_position() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Position",
        "orphan:AAPL",
        {"ticker": "AAPL", "quantity": 1, "opened_price_cents": 9900},
    )

    lifecycle = position_lifecycle(graph, "orphan:AAPL")

    assert lifecycle is not None
    assert lifecycle.status == "open"
    assert lifecycle.close_trigger is None
    assert lifecycle.run_id is None
    assert lifecycle.recommendation_confidence is None
    assert lifecycle.narrative_text is None
    assert position_lifecycle(graph, "missing") is None


def test_all_position_lifecycles_returns_present_positions_only() -> None:
    graph = InMemoryGraphStore()
    _seed_full_lifecycle(graph)
    graph.merge_node(
        "Position",
        "pm-run:MSFT",
        {
            "run_id": "pm-run",
            "ticker": "MSFT",
            "quantity": 1,
            "opened_price_cents": 8800,
        },
    )
    missing = _MissingPositionGraph()
    missing.merge_node("Position", "stale:AAPL", {"ticker": "AAPL"})

    assert [item.position_id for item in all_position_lifecycles(graph)] == [
        "pm-run:AAPL",
        "pm-run:MSFT",
    ]
    assert all_position_lifecycles(missing) == ()


def test_pending_flags_omits_resolved_flags() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Flag",
        "flag:resolved:warn",
        {"subject_ref": "resolved", "severity": "warn", "created_at": "1"},
    )
    graph.merge_node(
        "Flag",
        "flag:pending:critical",
        {"subject_ref": "pending", "severity": "critical", "created_at": "2"},
    )
    graph.merge_node(
        "FlagResolution",
        "resolution:flag:resolved:warn",
        {"subject_ref": "resolved", "severity": "warn"},
    )

    flags = pending_flags(graph)

    assert len(flags) == 1
    assert flags[0].subject_ref == "pending"
    assert flags[0].severity == "critical"
    assert pending_flags(InMemoryGraphStore()) == ()


def _seed_full_lifecycle(graph: InMemoryGraphStore) -> None:
    run = graph.merge_node("PMRun", "pm-run", {})
    recommendation = graph.merge_node(
        "Recommendation", "rec:AAPL", {"ticker": "AAPL", "confidence": 0.82}
    )
    order = graph.merge_node("OrderIntent", "pm-run:AAPL", {"ticker": "AAPL"})
    fill = graph.merge_node("Fill", "pm-run:AAPL:buy", {"ticker": "AAPL"})
    position = graph.merge_node(
        "Position",
        "pm-run:AAPL",
        {
            "run_id": "fallback-run",
            "ticker": "AAPL",
            "quantity": 3,
            "opened_price_cents": 10100,
        },
    )
    close = graph.merge_node("CloseDecision", "close:AAPL", {"trigger": "stop"})
    other = graph.merge_node("Other", "other:AAPL", {})
    narrative = graph.merge_node(
        "TradeNarrative", "narrative:pm-run:AAPL", {"summary": "AAPL closed on stop."}
    )
    graph.add_edge(order, run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(other, position, "OPENS")
    graph.add_edge(fill, position, "OPENS")
    graph.add_edge(order, recommendation, "APPROVES")
    graph.add_edge(close, position, "CLOSES")
    graph.add_edge(narrative, position, "NARRATES")


class _MissingPositionGraph(InMemoryGraphStore):
    def get_node(self, label: str, key: str) -> Node | None:
        del label, key
        return cast("Node | None", None)
