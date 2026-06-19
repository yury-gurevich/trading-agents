"""Reporter agent implementation.

Agent: reporter
Role: expose report and narrative capabilities over the message bus; publish
      report.snapshot.ready claim-check events on monitor.decisions.ready.
External I/O: none; graph backend is injected.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from agents.reporter.result import (
    build_snapshot,
    build_trade_narrative,
    degraded_narrative,
    degraded_snapshot,
)
from agents.reporter.settings import ReporterSettings
from contracts.monitor import CloseDecisionSet
from contracts.reporter import (
    CONTRACT,
    NarrativeRequest,
    ReportRequest,
    RunSnapshot,
    TradeNarrative,
)
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
    claim_check_read,
    claim_check_write,
)
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import MessageBus


class ReporterAgent(AgentBase):
    """Reporter boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: ReporterSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a reporter with injected bus, graph, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or ReporterSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {"report": self._report, "narrative": self._narrative}

    def bind(self) -> None:
        """Register RPC handlers and subscribe to monitor.decisions.ready."""
        super().bind()
        self.bus.subscribe("monitor.decisions.ready", self._on_decisions_ready)

    def _on_decisions_ready(self, event: dict[str, Any]) -> None:
        run_id: str | None = event.get("run_id")
        node = claim_check_read(self._graph, event)
        decisions = CloseDecisionSet.model_validate(node.props["decisions"])
        # pm_run_id threaded from execution→monitor so reporter finds the PMRun.
        pm_run_id = str(node.props.get("pm_run_id") or decisions.run_id)
        snapshot = self._report(ReportRequest(run_id=pm_run_id))
        claim_check_write(
            self.bus, self._graph,
            topic="report.snapshot.ready",
            label="ReportSnapshotResult",
            ref=f"snapshot:{run_id or uuid.uuid4().hex}",
            props={"snapshot": snapshot.model_dump(mode="json")},
            run_id=run_id,
        )

    def _report(self, request: BaseModel) -> RunSnapshot:
        report_request = ReportRequest.model_validate(request)
        with fault_boundary(
            self.sink,
            agent="reporter",
            module="agents.reporter.agent",
            capability="report",
            reraise=False,
        ) as capture:
            result = build_snapshot(self._graph, report_request.run_id)
        if capture.fault is not None:
            return degraded_snapshot(
                self._graph,
                report_request.run_id,
                "Reporter could not traverse the run graph.",
            )
        return result

    def _narrative(self, request: BaseModel) -> TradeNarrative:
        narrative_request = NarrativeRequest.model_validate(request)
        max_chars = self._settings.max_narrative_length_chars
        with fault_boundary(
            self.sink,
            agent="reporter",
            module="agents.reporter.agent",
            capability="narrative",
            reraise=False,
        ) as capture:
            result = build_trade_narrative(
                self._graph, narrative_request.position_id, max_chars=max_chars
            )
        if capture.fault is not None:
            return degraded_narrative(
                self._graph, narrative_request.position_id, max_chars=max_chars
            )
        return result
