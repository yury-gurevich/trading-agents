"""Reporter pub/sub dual-mode tests — P14.6.

Agent: reporter
Role: verify the reporter subscribes to monitor.decisions.ready, generates a snapshot,
      and publishes report.snapshot.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter import ReporterAgent
from agents.reporter.tests.helpers import RUN_ID, seed_full_graph
from contracts.common import Explanation, Provenance
from contracts.monitor import CloseDecisionSet
from contracts.reporter import RunSnapshot
from kernel import InMemoryGraphStore, InProcessBus, ReadyEvent, claim_check_read


def _minimal_decision_set(*, run_id: str = RUN_ID) -> CloseDecisionSet:
    return CloseDecisionSet(
        run_id=run_id,
        decisions=(),
        positions_checked=0,
        explanation=Explanation(summary="no positions to check"),
        provenance=Provenance(
            run_id=run_id,
            source_agent="monitor",
            graph_node_id=f"MonitorRun:{run_id}",
        ),
    )


def _seed_monitor_decision_result(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "run-rep-1",
    decision_run_id: str = RUN_ID,
) -> dict[str, object]:
    """Write MonitorDecisionResult node directly and return event dict."""
    decisions = _minimal_decision_set(run_id=decision_run_id)
    graph.merge_node(
        "MonitorDecisionResult",
        f"monitor:{run_id}",
        {"decisions": decisions.model_dump(mode="json")},
    )
    return ReadyEvent(
        topic="monitor.decisions.ready",
        label="MonitorDecisionResult",
        ref=f"monitor:{run_id}",
        run_id=run_id,
    ).model_dump(mode="json")


def _wire_with_decisions(
    *, run_id: str = "run-rep-1"
) -> tuple[InProcessBus, InMemoryGraphStore, dict[str, object]]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    seed_full_graph(graph)
    ReporterAgent(bus, graph=graph).bind()
    event = _seed_monitor_decision_result(graph, run_id=run_id)
    return bus, graph, event


def test_decisions_ready_triggers_snapshot_ready() -> None:
    bus, _, event = _wire_with_decisions()
    received: list[dict[str, object]] = []
    bus.subscribe("report.snapshot.ready", received.append)

    bus.publish("monitor.decisions.ready", event)

    assert len(received) == 1
    assert received[0]["topic"] == "report.snapshot.ready"
    assert str(received[0]["ref"]).startswith("snapshot:")


def test_report_snapshot_result_node_in_graph() -> None:
    bus, graph, event = _wire_with_decisions(run_id="run-rep-2")
    received: list[dict[str, object]] = []
    bus.subscribe("report.snapshot.ready", received.append)

    bus.publish("monitor.decisions.ready", event)

    node = claim_check_read(graph, received[0])
    assert node.label == "ReportSnapshotResult"
    assert "snapshot" in node.props


def test_report_snapshot_is_deserializable() -> None:
    bus, graph, event = _wire_with_decisions(run_id="run-rep-3")
    received: list[dict[str, object]] = []
    bus.subscribe("report.snapshot.ready", received.append)

    bus.publish("monitor.decisions.ready", event)

    node = claim_check_read(graph, received[0])
    snapshot = RunSnapshot.model_validate(node.props["snapshot"])
    assert isinstance(snapshot, RunSnapshot)


def test_run_id_propagated_in_snapshot_ready_event() -> None:
    bus, _, event = _wire_with_decisions(run_id="rep-run-99")
    received: list[dict[str, object]] = []
    bus.subscribe("report.snapshot.ready", received.append)

    bus.publish("monitor.decisions.ready", event)

    assert received[0]["run_id"] == "rep-run-99"


def test_existing_rpc_report_still_works() -> None:
    from agents.reporter.tests.helpers import report_message

    bus, _, _ = _wire_with_decisions()

    response = bus.request(report_message(RUN_ID))

    assert response.message_type == "response"
