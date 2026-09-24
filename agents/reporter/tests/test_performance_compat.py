"""Reporter performance contract compatibility tests.

Agent: reporter
Role: prove historical snapshot payloads still claim-check and deserialize.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.tests.helpers import RUN_ID
from contracts.reporter import RunSnapshot
from kernel import InMemoryGraphStore, InProcessBus, claim_check_read, claim_check_write


def test_legacy_snapshot_without_performance_metrics_deserializes() -> None:
    """RPT-TYP-03: legacy ReportSnapshotResult payloads remain valid."""
    graph = InMemoryGraphStore()
    bus = InProcessBus()
    events: list[dict[str, object]] = []
    bus.subscribe("report.snapshot.ready", events.append)
    legacy_snapshot = {
        "run_id": RUN_ID,
        "portfolio_metrics": {},
        "signal_metrics": {},
        "regime_attribution": {},
        "headline": {"summary": "legacy", "evidence_refs": []},
        "provenance": {
            "run_id": RUN_ID,
            "source_agent": "reporter",
            "graph_node_id": "Snapshot:legacy",
            "incident_refs": [],
        },
    }
    claim_check_write(
        bus,
        graph,
        topic="report.snapshot.ready",
        label="ReportSnapshotResult",
        ref="legacy",
        props={"snapshot": legacy_snapshot},
        run_id=RUN_ID,
    )

    node = claim_check_read(graph, events[0])
    snapshot = RunSnapshot.model_validate(node.props["snapshot"])

    assert snapshot.performance_metrics == {}
