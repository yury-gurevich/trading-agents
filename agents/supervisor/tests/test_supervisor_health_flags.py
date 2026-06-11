"""Supervisor health and flag tests.

Agent: supervisor
Role: verify system status, human flags, and degraded graph-write paths.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.supervisor import SupervisorAgent
from agents.supervisor.domain.health import compute_health
from agents.supervisor.store import resolve_flag, resolve_flag_by_subject
from contracts.common import Provenance
from contracts.operator import TypedIntent
from contracts.supervisor import (
    DispatchResult,
    FlagRequest,
    MasterReport,
    StatusRequest,
)
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus, Node

if TYPE_CHECKING:
    import pytest

    from kernel import GraphStore


def test_system_status_reports_empty_fault_flag_and_snapshot_states() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    empty = _status(bus)
    assert empty.healthy is True
    assert empty.open_incidents == 0
    graph.merge_node("Fault", "fault:one", {"status": "pending"})
    faulted = _status(bus)
    assert faulted.healthy is False
    assert faulted.open_incidents == 1
    graph.merge_node(
        "Flag",
        "flag:critical",
        {"status": "pending", "severity": "critical"},
    )
    graph.merge_node("Snapshot", "snapshot:latest", {"created_at": "2026-06-11"})
    report = _status(bus)
    assert report.pending_human_flags == 1
    assert report.last_successful_run == "snapshot:latest"


def test_system_status_ignores_resolved_faults_and_warn_flags() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Fault", "fault:resolved", {"status": "resolved"})
    graph.merge_node("Flag", "flag:warn", {"status": "pending", "severity": "warn"})
    graph.merge_node(
        "Flag", "flag:resolved", {"subject_ref": "resolved", "severity": "critical"}
    )
    graph.merge_node(
        "FlagResolution",
        "resolution:flag:resolved:critical",
        {"subject_ref": "resolved", "severity": "critical"},
    )
    assert _status(_bound_bus(graph)).healthy is True


def test_flag_for_human_writes_idempotent_pending_flag() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    request = FlagRequest(subject_ref="risk", severity="critical", reason="check")
    first = _flag(bus, request)
    second = _flag(bus, request)
    assert first.accepted is True
    assert second.accepted is True
    assert _node_count(graph, "Flag") == 1
    flag = graph.get_node("Flag", "flag:risk:critical")
    assert flag is not None
    assert flag.props["status"] == "pending"


def test_failure_paths_return_degraded_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = SupervisorAgent(InProcessBus(), graph=cast("GraphStore", _BrokenGraph()))
    assert agent._dispatch_intent(_intent("run")).accepted is False
    assert (
        agent._flag_for_human(
            FlagRequest(subject_ref="x", severity="warn", reason="x")
        ).accepted
        is False
    )
    monkeypatch.setattr("agents.supervisor.agent.compute_health", _raise_health)
    assert agent._system_status(StatusRequest()).healthy is False


def test_store_resolution_fallbacks() -> None:
    graph = InMemoryGraphStore()
    assert resolve_flag(graph, "missing", "warn") is None
    flag = graph.merge_node("Flag", "flag:subject:warn", {"subject_ref": "subject"})
    first = resolve_flag(graph, "subject", "warn")
    second = resolve_flag(graph, "subject", "warn")
    assert first == second
    assert list(graph.ancestors(flag, max_depth=1, edge_types={"RESOLVES"}))
    assert compute_health(_EmptyGraph(), None)["healthy"] is True  # type: ignore[arg-type]


def test_resolve_flag_by_subject_matches_only_unresolved_flags() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Flag",
        "flag:risk:critical",
        {"subject_ref": "risk", "severity": "critical"},
    )

    assert resolve_flag_by_subject(graph, "") is False
    assert resolve_flag_by_subject(graph, "missing") is False
    assert resolve_flag_by_subject(graph, "risk") is True
    assert graph.get_node("FlagResolution", "resolution:flag:risk:critical")
    assert resolve_flag_by_subject(graph, "risk") is False


def _bound_bus(graph: InMemoryGraphStore) -> InProcessBus:
    bus = InProcessBus()
    SupervisorAgent(bus, graph=graph).bind()
    return bus


def _status(bus: InProcessBus) -> MasterReport:
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


def _flag(bus: InProcessBus, request: FlagRequest) -> DispatchResult:
    response = bus.request(
        AgentMessage(
            sender="operator",
            recipient="supervisor",
            message_type="request",
            capability="flag_for_human",
            payload=request.model_dump(mode="json"),
        )
    )
    return DispatchResult.model_validate(response.payload)


def _intent(family: str) -> TypedIntent:
    return TypedIntent(
        family=family,  # type: ignore[arg-type]
        parameters={},
        requires_confirmation=family in {"run", "approve", "reject", "modify"},
        provenance=Provenance(run_id=f"intent-{family}", source_agent="operator"),
    )


def _node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))


def _raise_health(graph: GraphStore, run_id: str | None) -> dict[str, object]:
    raise RuntimeError("health failed")


class _BrokenGraph:
    def get_node(self, label: str, key: str) -> Node | None:
        return None

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        return ()

    def merge_node(
        self,
        label: str,
        key: str,
        props: dict[str, object],
        *,
        schema_version: int = 1,
    ) -> Node:
        raise RuntimeError("graph write failed")


class _EmptyGraph:
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        del label
        return ()
