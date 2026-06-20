"""Analyst pub/sub dual-mode tests — P14.4.

Agent: analyst
Role: verify the analyst subscribes to scan.candidates.ready, analyzes, and publishes
      analysis.recommendations.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.tests.helpers import bars, candidate, candidate_set, wire_analyst
from contracts.analyst import RecommendationSet
from kernel import InMemoryGraphStore, InProcessBus, ReadyEvent, claim_check_read

if TYPE_CHECKING:
    from contracts.scanner import CandidateSet


def _seed_scan_result(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "run-1",
    cs: CandidateSet | None = None,
) -> dict[str, object]:
    """Write a ScanResult node directly (no publish) and return its ready-event dict.

    This simulates what the scanner would have written before announcing the event,
    without triggering the analyst's subscriber prematurely.
    """
    if cs is None:
        cs = candidate_set(candidate())
    graph.merge_node(
        "ScanResult", f"scan:{run_id}", {"candidates": cs.model_dump(mode="json")}
    )
    return ReadyEvent(
        topic="scan.candidates.ready",
        label="ScanResult",
        ref=f"scan:{run_id}",
        run_id=run_id,
    ).model_dump(mode="json")


def _wire_with_candidate(
    *, run_id: str = "run-1"
) -> tuple[InProcessBus, InMemoryGraphStore, dict[str, object]]:
    bus, graph, _ = wire_analyst(source_bars=bars())
    graph.merge_node("Candidate", "scan-fixture:AAPL", {"ticker": "AAPL"})
    event = _seed_scan_result(graph, run_id=run_id)
    return bus, graph, event


def test_candidates_ready_triggers_recommendations_ready() -> None:
    """ANLZ-IN-02 / ANLZ-TRG-02 / ANLZ-OUT-05: scan.candidates.ready → claim-check
    resolved → analyze → analysis.recommendations.ready emitted."""
    bus, _, event = _wire_with_candidate()
    received: list[dict[str, object]] = []
    bus.subscribe("analysis.recommendations.ready", received.append)

    bus.publish("scan.candidates.ready", event)

    assert len(received) == 1
    assert received[0]["topic"] == "analysis.recommendations.ready"
    assert str(received[0]["ref"]).startswith("analysis:")


def test_recommendation_result_node_in_graph() -> None:
    """ANLZ-STA-02 / ANLZ-OBS-01: result node written to graph; append-only."""
    bus, graph, event = _wire_with_candidate(run_id="run-2")
    received: list[dict[str, object]] = []
    bus.subscribe("analysis.recommendations.ready", received.append)

    bus.publish("scan.candidates.ready", event)

    node = claim_check_read(graph, received[0])
    assert node.label == "RecommendationResult"
    assert "recommendations" in node.props


def test_recommendation_result_is_deserializable() -> None:
    """ANLZ-TYP-01: graph node deserialises to RecommendationSet per contract."""
    bus, graph, event = _wire_with_candidate(run_id="run-3")
    received: list[dict[str, object]] = []
    bus.subscribe("analysis.recommendations.ready", received.append)

    bus.publish("scan.candidates.ready", event)

    node = claim_check_read(graph, received[0])
    rec_set = RecommendationSet.model_validate(node.props["recommendations"])
    assert isinstance(rec_set, RecommendationSet)


def test_run_id_propagated_in_ready_event() -> None:
    """ANLZ-IDM-02: run_id threaded from CandidateSet to recommendations.ready."""
    bus, _, event = _wire_with_candidate(run_id="my-run-99")
    received: list[dict[str, object]] = []
    bus.subscribe("analysis.recommendations.ready", received.append)

    bus.publish("scan.candidates.ready", event)

    assert received[0]["run_id"] == "my-run-99"


def test_existing_rpc_analyze_still_works() -> None:
    from agents.analyst.tests.helpers import analyze_message

    bus, _graph, _ = wire_analyst(source_bars=bars())
    scan = candidate_set(candidate())

    response = bus.request(analyze_message(scan))

    assert response.message_type == "response"
