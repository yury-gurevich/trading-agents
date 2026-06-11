"""CLI narrative and approval command tests.

Agent: surfaces
Role: verify Sprint 20 narrative display and approval command behavior.
External I/O: none.
"""

from __future__ import annotations

import json
from io import StringIO

from contracts.common import Provenance
from contracts.supervisor import DispatchResult
from kernel import FakeLLMClient, InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import test_context as build_context
from surfaces.render import render_approve


def test_cli_narrative_renders_run_stories_or_missing_message() -> None:
    graph = InMemoryGraphStore()
    _seed_narrative(graph)
    output = StringIO()
    missing = StringIO()

    main(["narrative", "run-a"], context=build_context(graph=graph), stdout=output)
    main(["narrative", "missing"], context=build_context(graph=graph), stdout=missing)

    assert "AAPL" in output.getvalue()
    assert "AAPL closed on target." in output.getvalue()
    assert "no narratives for run missing" in missing.getvalue()


def test_cli_approve_resolves_flag_or_accepts_noop() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Flag",
        "flag:run/test-123:critical",
        {
            "subject_ref": "run/test-123",
            "severity": "critical",
            "created_at": "now",
        },
    )
    llm = FakeLLMClient(
        {
            "approve": json.dumps(
                {
                    "outcome": "intent",
                    "family": "approve",
                    "parameters": {"target": "run/test-123"},
                }
            )
        }
    )
    output = StringIO()
    noop = StringIO()

    main(
        ["approve", "run/test-123"],
        context=build_context(graph=graph, llm=llm),
        stdout=output,
    )
    main(
        ["approve", "unknown"],
        context=build_context(graph=graph, llm=llm),
        stdout=noop,
    )

    assert "approved: run/test-123" in output.getvalue()
    assert "supervisor.resolve_flag" in output.getvalue()
    assert graph.get_node("FlagResolution", "resolution:flag:run/test-123:critical")
    assert "approved: unknown" in noop.getvalue()


def test_cli_approve_requires_approve_intent() -> None:
    output = StringIO()

    main(["approve", "risk"], context=build_context(), stdout=output)

    assert "could not interpret approve command for: risk" in output.getvalue()


def test_render_approve_refusal_includes_reason() -> None:
    refused = DispatchResult(
        accepted=False,
        rejection="blocked",
        provenance=Provenance(run_id="approval", source_agent="supervisor"),
    )
    quiet_refusal = DispatchResult(
        accepted=False,
        provenance=Provenance(run_id="quiet", source_agent="supervisor"),
    )
    no_route = DispatchResult(
        accepted=True,
        provenance=Provenance(run_id="approval", source_agent="supervisor"),
    )

    assert "reason: blocked" in render_approve(refused, "approval")
    assert render_approve(quiet_refusal, "quiet") == "approve refused: quiet"
    assert render_approve(no_route, "approval") == "approved: approval"


def _seed_narrative(graph: InMemoryGraphStore) -> None:
    position = graph.merge_node(
        "Position",
        "run-a:AAPL",
        {"run_id": "run-a", "ticker": "AAPL"},
    )
    narrative = graph.merge_node(
        "TradeNarrative",
        "narrative:run-a:AAPL",
        {
            "run_id": "run-a",
            "position_id": "run-a:AAPL",
            "summary": "AAPL closed on target.",
        },
    )
    graph.add_edge(narrative, position, "NARRATES")
