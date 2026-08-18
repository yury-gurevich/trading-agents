"""Supervisor Fault incident health tests.

Agent: supervisor
Role: verify live Fault incident scoping and append-only retirement evidence.
External I/O: none.
"""

from __future__ import annotations

from agents.supervisor import SupervisorAgent
from agents.supervisor.fault_resolution import resolve_fault
from contracts.supervisor import MasterReport, StatusRequest
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus


def test_system_status_scopes_fault_incidents_to_latest_run_day() -> None:
    """SUP-OUT-02 / SUP-STA-02 / SUP-IDM-01: old Faults do not pin health."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "BrokerPositionSnapshot",
        "broker-position-snapshot:current",
        {"created_at": "2026-08-18T04:00:00+00:00"},
    )
    graph.merge_node(
        "Fault",
        "fault:closed-july",
        {
            "status": "pending",
            "severity": "error",
            "occurred_at": "2026-07-30T22:30:00+00:00",
        },
    )
    graph.merge_node(
        "Fault",
        "fault:current-error",
        {
            "status": "pending",
            "severity": "error",
            "occurred_at": "2026-08-18T04:22:00+00:00",
        },
    )

    before = _status(graph)

    assert before.healthy is False
    assert before.open_incidents == 1

    graph.merge_node(
        "FaultResolution",
        "resolution:fault:current-error",
        {
            "fault_key": "fault:current-error",
            "resolved_at": "2026-08-18T05:00:00+00:00",
        },
    )

    report = _status(graph)

    assert report.healthy is True
    assert report.open_incidents == 0
    current = graph.get_node("Fault", "fault:current-error")
    assert current is not None
    assert current.props["status"] == "pending"


def test_resolve_fault_appends_resolution_without_mutating_fault() -> None:
    """SUP-STA-02 / SUP-OBS-03: Fault retirement appends resolution evidence."""
    graph = InMemoryGraphStore()
    fault = graph.merge_node(
        "Fault",
        "fault:current-error",
        {"status": "pending", "severity": "error"},
    )

    first = resolve_fault(
        graph,
        fault,
        resolved_by="test",
        reason="operator inspected the incident",
    )
    second = resolve_fault(
        graph,
        fault,
        resolved_by="test",
        reason="operator inspected the incident",
    )

    assert first == second
    assert first.props["fault_key"] == fault.key
    current = graph.get_node("Fault", fault.key)
    assert current is not None
    assert current.props["status"] == "pending"
    assert tuple(graph.ancestors(fault, max_depth=1, edge_types={"RESOLVES"})) == (
        first,
    )


def _status(graph: InMemoryGraphStore) -> MasterReport:
    bus = InProcessBus()
    SupervisorAgent(bus, graph=graph).bind()
    response = bus.request(
        AgentMessage(
            sender="operator",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload=StatusRequest().model_dump(mode="json"),
        )
    )
    return MasterReport.model_validate(response.payload)
