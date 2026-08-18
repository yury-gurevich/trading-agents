"""Fault incident health projection tests.

Agent: kernel
Role: prove immutable Fault evidence can be scoped into live incidents.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.fault_incidents import live_fault_incidents


def test_live_fault_incidents_uses_latest_snapshot_day_and_resolutions() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "BrokerPositionSnapshot",
        "broker-position-snapshot:current",
        {"created_at": "2026-08-18T04:00:00+00:00"},
    )
    _fault(graph, "old-error", "2026-07-30T22:30:00+00:00", "error")
    _fault(graph, "current-warning", "2026-08-18T04:20:00+00:00", "warning")
    _fault(graph, "current-error", "2026-08-18T04:22:00+00:00", "error")
    _fault(graph, "current-critical", "2026-08-18T04:23:00+00:00", "critical")
    _fault(
        graph,
        "current-resolved-status",
        "2026-08-18T04:24:00+00:00",
        "error",
        status="resolved",
    )
    _fault(graph, "current-resolved-node", "2026-08-18T04:25:00+00:00", "error")
    graph.merge_node(
        "FaultResolution",
        "resolution:fault:current-resolved-node",
        {"fault_key": "fault:current-resolved-node"},
    )

    incidents = live_fault_incidents(graph)

    assert [node.key for node in incidents] == [
        "fault:current-error",
        "fault:current-critical",
    ]


def test_live_fault_incidents_falls_back_to_latest_fault_day() -> None:
    graph = InMemoryGraphStore()
    _fault(graph, "old-error", "2026-07-30T22:30:00+00:00", "error")
    _fault(graph, "latest-error", "2026-08-18T04:22:00+00:00", "error")

    incidents = live_fault_incidents(graph)

    assert [node.key for node in incidents] == ["fault:latest-error"]


def test_live_fault_incidents_keeps_legacy_missing_dates_live() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Fault", "fault:legacy", {"status": "pending"})

    incidents = live_fault_incidents(graph)

    assert [node.key for node in incidents] == ["fault:legacy"]


def _fault(
    graph: InMemoryGraphStore,
    name: str,
    occurred_at: str,
    severity: str,
    *,
    status: str = "pending",
) -> None:
    graph.merge_node(
        "Fault",
        f"fault:{name}",
        {"status": status, "severity": severity, "occurred_at": occurred_at},
    )
