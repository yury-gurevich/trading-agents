"""CLI incident and explain command tests.

Agent: surfaces
Role: verify Sprint 21 operator-facing recovery and explanation commands.
External I/O: none.
"""

from __future__ import annotations

from io import StringIO

from kernel import InMemoryGraphStore, InProcessBus
from surfaces.cli import main
from surfaces.context import SurfaceContext
from surfaces.context import test_context as build_context


def test_cli_incidents_renders_empty_or_seeded_fault() -> None:
    empty = StringIO()
    main(["incidents"], context=build_context(), stdout=empty)
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fault",
        "fault:analyst:boom",
        {
            "source_agent": "analyst",
            "capability": "analyze",
            "severity": "critical",
            "message": "analysis failed",
            "occurred_at": "2026-06-11T00:00:00+00:00",
        },
    )
    output = StringIO()
    main(["incidents"], context=build_context(graph=graph), stdout=output)

    assert "no open incidents" in empty.getvalue()
    assert "analyst" in output.getvalue()
    assert "analysis failed" in output.getvalue()


def test_cli_explain_renders_reporter_narrative_summary() -> None:
    graph = InMemoryGraphStore()
    _seed_trade_lineage(graph)
    output = StringIO()

    main(["explain", "run-a:AAPL"], context=build_context(graph=graph), stdout=output)

    assert "Narrative - position run-a:AAPL" in output.getvalue()
    assert "AAPL scanned" in output.getvalue()
    assert "ref: reporter.graph" in output.getvalue()


def test_cli_explain_reports_bus_error() -> None:
    output = StringIO()
    context = SurfaceContext(InMemoryGraphStore(), InProcessBus())

    main(["explain", "missing"], context=context, stdout=output)

    assert "explain failed for position: missing" in output.getvalue()


def _seed_trade_lineage(graph: InMemoryGraphStore) -> None:
    run = graph.merge_node("PMRun", "run-a", {"approved_count": 1})
    order = graph.merge_node(
        "OrderIntent",
        "run-a:AAPL",
        {
            "ticker": "AAPL",
            "action": "buy",
            "quantity": 3,
            "est_price_cents": 10100,
            "stop_pct": 0.05,
            "target_pct": 0.10,
        },
    )
    fill = graph.merge_node("Fill", "run-a:AAPL:buy", {"ticker": "AAPL"})
    position = graph.merge_node(
        "Position",
        "run-a:AAPL",
        {"run_id": "run-a", "ticker": "AAPL", "opened_price_cents": 10100},
    )
    recommendation = graph.merge_node(
        "Recommendation",
        "analyst:AAPL",
        {"ticker": "AAPL", "confidence": 0.82, "technical_score": 0.77},
    )
    candidate = graph.merge_node(
        "Candidate", "scan:AAPL", {"ticker": "AAPL", "rank": 1, "score": 0.91}
    )
    scan = graph.merge_node("ScanRun", "scan", {"created_at": "2026-06-11"})
    close = graph.merge_node(
        "CloseDecision",
        "close:run-a:AAPL",
        {"trigger": "target", "rationale": "Target was reached."},
    )
    graph.add_edge(order, run, "EMITTED_BY")
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(fill, position, "OPENS")
    graph.add_edge(order, recommendation, "APPROVES")
    graph.add_edge(recommendation, candidate, "DERIVED_FROM")
    graph.add_edge(candidate, scan, "SURVIVED")
    graph.add_edge(close, position, "CLOSES")
