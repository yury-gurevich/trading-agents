"""Dashboard state projection tests — flags, positions, recovery, bundle.

Agent: surfaces
Role: verify run-day scoping, the graph-vs-broker join, the DL-36 ladder
      projection, and the LLM context bundle's shape.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import Any, cast

import surfaces.dashboard.projections_state as state
from kernel import InMemoryGraphStore
from orchestration.start import place_run_request

DAY = date(2026, 7, 9)


def _graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="r1", tickers=("AAPL",), as_of=DAY)
    return graph


def test_flags_scoped_to_day_plus_pending() -> None:
    graph = _graph()
    graph.merge_node(
        "Flag",
        "f-run-day",
        {
            "severity": "critical",
            "reason": "qty_mismatch CSCO",
            "status": "resolved",
            "created_at": "2026-07-09T22:33:32+00:00",
            "subject_ref": "x",
        },
    )
    graph.merge_node(
        "Flag",
        "f-old-pending",
        {
            "severity": "warn",
            "reason": "old but open",
            "status": "pending",
            "created_at": "2026-07-01T00:00:00+00:00",
            "subject_ref": "y",
        },
    )
    graph.merge_node(
        "Flag",
        "f-old-resolved",
        {
            "severity": "warn",
            "reason": "old and done",
            "status": "resolved",
            "created_at": "2026-07-01T00:00:00+00:00",
            "subject_ref": "z",
        },
    )
    keys = [r["key"] for r in state.run_flags(graph, "r1")]
    assert set(keys) == {"f-run-day", "f-old-pending"}


def test_flags_unknown_run_returns_only_pending() -> None:
    graph = _graph()
    graph.merge_node(
        "Flag",
        "f-pending",
        {
            "severity": "critical",
            "reason": "r",
            "status": "pending",
            "created_at": "2026-07-02T00:00:00+00:00",
            "subject_ref": "s",
        },
    )
    assert [r["key"] for r in state.run_flags(graph, "no-such-run")] == ["f-pending"]


def test_positions_join_and_divergence() -> None:
    graph = _graph()
    graph.merge_node(
        "Position", "p1", {"ticker": "CSCO", "quantity": 88, "status": "open"}
    )
    graph.merge_node(
        "Position", "p2", {"ticker": "AMD", "quantity": 19, "status": "open"}
    )
    graph.merge_node(
        "Position", "p-closed", {"ticker": "WFC", "quantity": 5, "status": "closed"}
    )
    graph.merge_node(
        "Position",
        "p-superseded",
        {
            "ticker": "HPE",
            "quantity": 1,
            "status": "open",
            "broker_superseded_by": "p9",
        },
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "s-old",
        {
            "created_at": "2026-07-08T00:00:00+00:00",
            "holdings": [{"ticker": "CSCO", "quantity": 88}],
        },
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "s-new",
        {
            "created_at": "2026-07-09T22:33:32+00:00",
            "holdings": [
                {"ticker": "CSCO", "quantity": 177},
                {"ticker": "BAC", "quantity": 171},
            ],
        },
    )
    result = state.run_positions(graph, "r1")
    assert result["snapshot_key"] == "s-new"
    rows = {
        cast("str", r["ticker"]): r
        for r in cast("list[dict[str, Any]]", result["rows"])
    }
    assert set(rows) == {"AMD", "BAC", "CSCO"}
    assert rows["CSCO"]["graph_qty"] == 88
    assert rows["CSCO"]["broker_qty"] == 177
    assert rows["CSCO"]["match"] is False
    assert rows["AMD"]["broker_qty"] is None
    assert rows["BAC"]["graph_qty"] is None


def test_positions_without_snapshot() -> None:
    graph = _graph()
    graph.merge_node(
        "Position", "p1", {"ticker": "AMD", "quantity": 19, "status": "open"}
    )
    result = state.run_positions(graph, "r1")
    assert result["snapshot_key"] is None
    assert result["snapshot_at"] is None
    rows = cast("list[dict[str, Any]]", result["rows"])
    assert rows[0]["broker_qty"] is None


def test_recovery_ladder_scoping() -> None:
    graph = _graph()
    graph.merge_node(
        "Escalation",
        "e-open",
        {
            "agent_type": "provider",
            "failed_credentials": ["FINNHUB"],
            "mode": "manual",
            "auto_attempts": 1,
            "status": "open",
            "created_at": "2026-07-01T00:00:00+00:00",
        },
    )
    graph.merge_node(
        "Escalation",
        "e-old-resolved",
        {
            "agent_type": "scanner",
            "failed_credentials": [],
            "mode": "manual",
            "auto_attempts": 0,
            "status": "resolved",
            "created_at": "2026-07-01T01:00:00+00:00",
        },
    )
    graph.merge_node(
        "RemediationPlan",
        "plan-day",
        {
            "escalation_key": "e-open",
            "remediation": "reseed-secret",
            "rationale": "stale",
            "auto_eligible": True,
            "status": "executed",
            "created_at": "2026-07-09T01:00:00+00:00",
        },
    )
    result = state.run_recovery(graph, "r1")
    esc = cast("list[dict[str, Any]]", result["escalations"])
    plans = cast("list[dict[str, Any]]", result["remediation_plans"])
    assert [e["key"] for e in esc] == ["e-open"]
    assert [p["key"] for p in plans] == ["plan-day"]
