"""Trading deliberation posture acceptance tests for S185.

Agent: orchestration
Role: prove advisory deliberation fail-open must be attributable, not invisible.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore, Node
from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation


def _fail_open_graph(
    *,
    posture: str | None = "advisory",
    status: str = "applied_failed_open",
    reason: str = "RuntimeError: provider unavailable",
) -> tuple[InMemoryGraphStore, Node]:
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node("PMRun", "pm-run", {})
    delib = graph.merge_node(
        "DeliberationRun",
        "delib-run",
        {
            "verdicts": {"AAPL": "uphold"},
            "vetoed_tickers": (),
            "debates": {"AAPL": {"verdict": "uphold", "turns": []}},
            "real_debate_count": 0,
            "failed_open_count": 1,
            "failed_open_tickers": ("AAPL",),
            "failed_open_reason": reason,
        },
    )
    props: dict[str, object] = {
        "deliberation_status": status,
        "submitted": 1,
    }
    if posture is not None:
        props["deliberation_posture"] = posture
    execution = graph.merge_node("ExecutionRun", "exec-run", props)
    graph.add_edge(pm_run, delib, "DELIBERATED_BY")
    graph.add_edge(pm_run, execution, "EXECUTED_BY")
    return graph, delib


def test_advisory_fail_open_passes_when_attributed() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: advisory fail-open is green only with cause."""
    graph, node = _fail_open_graph()

    found = breaches(deliberation(graph, node))

    assert found == ()


def test_advisory_fail_open_fails_without_recorded_posture() -> None:
    """EXEC-OUT-09: advisory acceptance needs the posture on ExecutionRun."""
    graph, node = _fail_open_graph(posture=None)

    found = breaches(deliberation(graph, node))

    assert any(breach.key == "advisory_attribution" for breach in found)


def test_advisory_fail_open_fails_without_reason() -> None:
    """EXEC-OBS-04: advisory fail-open needs the recorded failure reason."""
    graph, node = _fail_open_graph(reason="")

    found = breaches(deliberation(graph, node))

    assert any(breach.key == "advisory_attribution" for breach in found)


def test_advisory_fail_open_fails_with_unattributable_status() -> None:
    """EXEC-OBS-04: advisory acceptance names allowed fail-open statuses."""
    graph, node = _fail_open_graph(status="waiting")

    found = breaches(deliberation(graph, node))

    assert any(breach.key == "advisory_attribution" for breach in found)


def test_deliberation_fails_without_linked_execution_run() -> None:
    """EXEC-OUT-09: posture is missing when no ExecutionRun is linked."""
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "DeliberationRun",
        "orphan-delib",
        {
            "verdicts": {"AAPL": "uphold"},
            "vetoed_tickers": (),
            "debates": {"AAPL": {"verdict": "uphold", "turns": []}},
            "real_debate_count": 1,
            "failed_open_count": 0,
        },
    )

    view = deliberation(graph, node)
    found = breaches(view)

    assert not any(output.startswith("posture=") for output in view.outputs)
    assert any(breach.key == "deliberation_posture" for breach in found)
