"""Execution agent implementation.

Agent: execution
Role: submit approved intents through the idempotent broker port;
      publish execution.fills.ready claim-check events on portfolio.orders.ready.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from agents.execution.broker import PaperBroker
from agents.execution.domain.reconcile import reconcile_fills
from agents.execution.run import run_submit
from agents.execution.settings import ExecutionSettings
from agents.execution.stage_flow import promote_stage
from agents.execution.store import (
    current_stage_from_graph,
    write_reconciliation,
)
from contracts.execution import (
    CONTRACT,
    ExecutionResult,
    PromoteStageRequest,
    PromoteStageResult,
    ReconcileRequest,
    ReconcileResult,
    StageStatus,
    StageStatusRequest,
)
from contracts.portfolio_manager import OrderIntentSet
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
    claim_check_read,
    claim_check_write,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.execution.broker import Broker, BrokerFill
    from kernel import MessageBus


class ExecutionAgent(AgentBase):
    """Execution boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        broker: Broker | None = None,
        settings: ExecutionSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create execution with injected graph, broker, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or ExecutionSettings()
        self._broker = broker or PaperBroker(slippage_bps=self._settings.slippage_bps)
        self.sink = sink if sink is not None else CollectingFaultSink()
        self._recorded: dict[str, BrokerFill] = {}
        self.handlers = {
            "submit": self._submit,
            "reconcile": self._reconcile,
            "stage_status": self._stage_status,
            "promote_stage": self._promote_stage,
        }

    def bind(self) -> None:
        """Register RPC handlers and subscribe to portfolio.orders.ready."""
        super().bind()
        self.bus.subscribe("portfolio.orders.ready", self._on_orders_ready)

    def _on_orders_ready(self, event: dict[str, Any]) -> None:
        run_id: str | None = event.get("run_id")
        node = claim_check_read(self._graph, event)
        orders = OrderIntentSet.model_validate(node.props["orders"])
        result = self._submit(orders)
        claim_check_write(
            self.bus,
            self._graph,
            topic="execution.fills.ready",
            label="ExecutionResultEvent",
            ref=f"execution:{run_id or uuid.uuid4().hex}",
            # pm_run_id is orders.run_id — threaded downstream so monitor/reporter
            # can find the PMRun node without an extra graph lookup.
            props={
                "result": result.model_dump(mode="json"),
                "pm_run_id": orders.run_id,
            },
            run_id=run_id,
        )

    def _submit(self, request: BaseModel) -> ExecutionResult:
        order_set = OrderIntentSet.model_validate(request)
        return run_submit(
            self._graph,
            self._broker,
            self.sink,
            self._recorded,
            order_set,
            default_stage=self._settings.stage,
        )

    def _reconcile(self, request: BaseModel) -> ReconcileResult:
        ReconcileRequest.model_validate(request)
        matched, discrepancies = reconcile_fills(
            tuple(self._recorded.values()), self._broker.fills()
        )
        provenance = write_reconciliation(
            self._graph, matched=matched, discrepancies=discrepancies
        )
        return ReconcileResult(
            matched=matched,
            discrepancies=discrepancies,
            provenance=provenance,
        )

    def _stage_status(self, request: BaseModel) -> StageStatus:
        StageStatusRequest.model_validate(request)
        return StageStatus(
            stage=current_stage_from_graph(self._graph, self._settings.stage),
            idempotent=True,
            reason="stage is graph-authoritative; submissions keep stable keys",
        )

    def _promote_stage(self, request: BaseModel) -> PromoteStageResult:
        stage_request = PromoteStageRequest.model_validate(request)
        return promote_stage(self._graph, self.bus, self._settings, stage_request)
