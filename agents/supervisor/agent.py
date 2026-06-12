"""Supervisor agent implementation.

Agent: supervisor
Role: expose P4 message-lineage and fault-recording capabilities over the bus.
External I/O: none; graph backend is injected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor.domain.gate import dispatch_intent
from agents.supervisor.domain.health import compute_health
from agents.supervisor.result import failed_health, master_report, provenance, rejected
from agents.supervisor.settings import SupervisorSettings
from agents.supervisor.store import (
    write_dispatch_run,
    write_fault,
    write_flag,
)
from contracts.common import Provenance
from contracts.operator import TypedIntent
from contracts.supervisor import (
    CONTRACT,
    DispatchResult,
    DispatchRunRecord,
    FlagRequest,
    MasterReport,
    StatusRequest,
)
from kernel import AgentBase, AgentFault, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import MessageBus


class SupervisorAgent(AgentBase):
    """Supervisor boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: SupervisorSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create supervisor with injected bus, graph, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or SupervisorSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "dispatch_intent": self._dispatch_intent,
            "system_status": self._system_status,
            "flag_for_human": self._flag_for_human,
            "record_dispatch_run": self._record_dispatch_run,
            "report_fault": self._report_fault,
        }

    def bind(self) -> None:
        """Register implemented supervisor capabilities."""
        for name, handler in self.handlers.items():
            capability = self.contract.capability(name)
            self.bus.register(
                self.contract.name, name, self._bus_handler(capability, handler)
            )

    def _record_dispatch_run(self, request: BaseModel) -> DispatchResult:
        record = DispatchRunRecord.model_validate(request)
        provenance: Provenance | None = None
        with fault_boundary(
            self.sink,
            agent="supervisor",
            module="agents.supervisor.agent",
            capability="record_dispatch_run",
            reraise=False,
        ) as capture:
            provenance = write_dispatch_run(
                self._graph,
                run_id=record.run_id,
                steps_attempted=record.steps_attempted,
                completed=record.completed,
                faults=record.faults,
                max_fault_message_chars=self._settings.max_fault_message_chars,
            )
        if capture.fault is not None:
            return rejected(record.run_id, "supervisor could not record dispatch run")
        assert provenance is not None
        return DispatchResult(accepted=True, provenance=provenance)

    # P5 additions below.
    def _dispatch_intent(self, request: BaseModel) -> DispatchResult:
        intent = TypedIntent.model_validate(request)
        result = rejected(intent.provenance.run_id, "supervisor dispatch failed")
        with fault_boundary(
            self.sink,
            agent="supervisor",
            module="agents.supervisor.agent",
            capability="dispatch_intent",
            reraise=False,
        ) as capture:
            result = dispatch_intent(self._graph, intent, bus=self.bus)
        if capture.fault is not None:
            return rejected(intent.provenance.run_id, "supervisor dispatch failed")
        return result

    def _system_status(self, request: BaseModel) -> MasterReport:
        status_request = StatusRequest.model_validate(request)
        health = failed_health()
        with fault_boundary(
            self.sink,
            agent="supervisor",
            module="agents.supervisor.agent",
            capability="system_status",
            reraise=False,
        ) as capture:
            health = compute_health(self._graph, status_request.run_id)
        if capture.fault is not None:
            health = failed_health()
        return master_report(status_request.run_id or "system-status", health)

    def _flag_for_human(self, request: BaseModel) -> DispatchResult:
        flag_request = FlagRequest.model_validate(request)
        result = rejected(flag_request.subject_ref, "supervisor could not flag")
        with fault_boundary(
            self.sink,
            agent="supervisor",
            module="agents.supervisor.agent",
            capability="flag_for_human",
            reraise=False,
        ) as capture:
            node = write_flag(
                self._graph,
                subject_ref=flag_request.subject_ref,
                severity=flag_request.severity,
                reason=flag_request.reason,
            )
            result = DispatchResult(
                accepted=True,
                provenance=provenance(flag_request.subject_ref, "Flag", node.key),
            )
        if capture.fault is not None:
            return rejected(flag_request.subject_ref, "supervisor could not flag")
        return result

    def _report_fault(self, request: BaseModel) -> DispatchResult:
        fault = AgentFault.model_validate(request)
        provenance: Provenance | None = None
        with fault_boundary(
            self.sink,
            agent="supervisor",
            module="agents.supervisor.agent",
            capability="report_fault",
            reraise=False,
        ) as capture:
            node = write_fault(
                self._graph,
                fault,
                max_message_chars=self._settings.max_fault_message_chars,
            )
            provenance = Provenance(
                run_id=f"fault:{node.key}",
                source_agent="supervisor",
                graph_node_id=f"{node.label}:{node.key}",
            )
        if capture.fault is not None:
            return rejected("fault", "supervisor could not record fault")
        assert provenance is not None
        return DispatchResult(accepted=True, provenance=provenance)
