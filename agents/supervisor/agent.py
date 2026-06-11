"""Supervisor agent implementation.

Agent: supervisor
Role: expose P4 message-lineage and fault-recording capabilities over the bus.
External I/O: none; graph backend is injected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor.settings import SupervisorSettings
from agents.supervisor.store import write_dispatch_run, write_fault
from contracts.common import Provenance
from contracts.supervisor import (
    CONTRACT,
    DispatchResult,
    DispatchRunRecord,
)
from kernel import AgentBase, AgentFault, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import MessageBus


class SupervisorAgent(AgentBase):
    """Minimal P4 supervisor boundary agent."""

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
            "record_dispatch_run": self._record_dispatch_run,
            "report_fault": self._report_fault,
        }

    def bind(self) -> None:
        """Register only P4 capabilities; P5 contract entries remain unhandled."""
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
            return _rejected(record.run_id, "supervisor could not record dispatch run")
        assert provenance is not None
        return DispatchResult(accepted=True, provenance=provenance)

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
            return _rejected("fault", "supervisor could not record fault")
        assert provenance is not None
        return DispatchResult(accepted=True, provenance=provenance)


def _rejected(run_id: str, reason: str) -> DispatchResult:
    return DispatchResult(
        accepted=False,
        rejection=reason,
        provenance=Provenance(run_id=run_id, source_agent="supervisor"),
    )
