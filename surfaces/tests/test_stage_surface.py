"""Stage surface tests.

Agent: surfaces
Role: verify read-only CLI and query projections for execution stage.
External I/O: none.
"""

from __future__ import annotations

from io import StringIO

from kernel import InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import test_context as build_context
from surfaces.queries.stage import current_stage, stage_history


def test_stage_queries_empty_and_history_order() -> None:
    graph = InMemoryGraphStore()
    assert current_stage(graph) == "paper"
    assert stage_history(graph) == ()
    _transition(graph, "paper", "broker_shadow", "1")
    _transition(graph, "broker_shadow", "live_manual", "2")

    history = stage_history(graph)

    assert current_stage(graph) == "live_manual"
    assert [item.to_stage for item in history] == ["broker_shadow", "live_manual"]


def test_cli_stage_renders_empty_and_transition_history() -> None:
    graph = InMemoryGraphStore()
    empty = StringIO()
    history = StringIO()

    main(["stage"], context=build_context(graph=graph), stdout=empty)
    _transition(graph, "paper", "broker_shadow", "2026-06-12T00:00:00+00:00")
    main(["stage"], context=build_context(graph=graph), stdout=history)

    assert "Execution stage: paper" in empty.getvalue()
    assert "Execution stage: broker_shadow" in history.getvalue()
    assert "paper -> broker_shadow" in history.getvalue()


def _transition(
    graph: InMemoryGraphStore, from_stage: str, to_stage: str, transitioned_at: str
) -> None:
    graph.merge_node(
        "StageTransition",
        f"stage:{to_stage}:{transitioned_at}",
        {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "reason": "fixture",
            "transitioned_at": transitioned_at,
        },
    )
