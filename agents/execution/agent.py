"""Execution agent implementation.

Agent: execution
Role: submit approved intents and close decisions through the idempotent broker port;
      publish execution.fills.ready claim-check events on portfolio.orders.ready.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from agents.execution.broker import PaperBroker
from agents.execution.domain.orders import (
    execution_run_id,
    order_from_close,
    order_from_intent,
)
from agents.execution.domain.reconcile import reconcile_fills
from agents.execution.domain.result import execution_result
from agents.execution.domain.submit import remember, submit_order
from agents.execution.live_gate import live_gate_rejected
from agents.execution.settings import ExecutionSettings
from agents.execution.stage_flow import promote_stage
from agents.execution.store import (
    current_stage_from_graph,
    write_fills,
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
from contracts.monitor import CloseDecisionSet
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
            "execute_close": self._execute_close,
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
        stage = current_stage_from_graph(self._graph, self._settings.stage)
        orders = tuple(
            order_from_intent(order_set, intent) for intent in order_set.approved
        )
        if stage not in ("paper", "broker_shadow"):
            return live_gate_rejected(self._graph, order_set, orders, stage)
        fills = tuple(
            submit_order(
                self._broker,
                self.sink,
                order,
                "submit",
            )
            for order in orders
        )
        remember(self._recorded, fills)
        run_id = execution_run_id("submit", order_set.run_id)
        provenance = write_fills(
            self._graph, run_id=run_id, fills=fills, order_set=order_set
        )
        return execution_result(run_id, stage, fills, provenance)

    def _execute_close(self, request: BaseModel) -> ExecutionResult:
        close_set = CloseDecisionSet.model_validate(request)
        stage = current_stage_from_graph(self._graph, self._settings.stage)
        orders = tuple(
            order_from_close(
                close_set,
                decision,
                quantity=self._settings.close_quantity,
                reference_price=self._settings.close_reference_price,
            )
            for decision in close_set.decisions
            if decision.decision == "close"
        )
        fills = tuple(
            submit_order(self._broker, self.sink, order, "execute_close")
            for order in orders
        )
        remember(self._recorded, fills)
        run_id = execution_run_id("close", close_set.run_id)
        provenance = write_fills(self._graph, run_id=run_id, fills=fills)
        return execution_result(run_id, stage, fills, provenance)

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
