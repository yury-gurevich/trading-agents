"""Execution agent implementation.

Agent: execution
Role: submit approved intents and close decisions through the idempotent broker port.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import BrokerRejectedError, PaperBroker
from agents.execution.domain.orders import (
    BrokerOrder,
    execution_run_id,
    fill_from_broker,
    order_from_close,
    order_from_intent,
    rejected_broker_fill,
)
from agents.execution.domain.reconcile import reconcile_fills
from agents.execution.settings import ExecutionSettings
from agents.execution.store import write_fills, write_reconciliation
from contracts.execution import (
    CONTRACT,
    ExecutionResult,
    ExecutionStage,
    Fill,
    ReconcileRequest,
    ReconcileResult,
    StageStatus,
    StageStatusRequest,
)
from contracts.monitor import CloseDecisionSet
from contracts.portfolio_manager import OrderIntentSet
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.execution.broker import Broker, BrokerFill
    from contracts.common import Provenance
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
        }

    def _submit(self, request: BaseModel) -> ExecutionResult:
        order_set = OrderIntentSet.model_validate(request)
        fills = tuple(
            self._submit_order(order_from_intent(order_set, intent), "submit")
            for intent in order_set.approved
        )
        self._remember(fills)
        run_id = execution_run_id("submit", order_set.run_id)
        provenance = write_fills(
            self._graph, run_id=run_id, fills=fills, order_set=order_set
        )
        return _execution_result(run_id, self._settings.stage, fills, provenance)

    def _execute_close(self, request: BaseModel) -> ExecutionResult:
        close_set = CloseDecisionSet.model_validate(request)
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
        fills = tuple(self._submit_order(order, "execute_close") for order in orders)
        self._remember(fills)
        run_id = execution_run_id("close", close_set.run_id)
        provenance = write_fills(self._graph, run_id=run_id, fills=fills)
        return _execution_result(run_id, self._settings.stage, fills, provenance)

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
            stage=self._settings.stage,
            idempotent=True,
            reason="paper broker submissions are keyed by stable idempotency keys",
        )

    def _submit_order(self, order: BrokerOrder, capability: str) -> BrokerFill:
        try:
            with fault_boundary(
                self.sink,
                agent="execution",
                module="agents.execution.agent",
                capability=capability,
                reraise=True,
            ):
                return self._broker.submit(
                    order.idempotency_key,
                    order.ticker,
                    order.side,
                    order.quantity,
                    order.limit_price,
                )
        except BrokerRejectedError as exc:
            return exc.fill
        except Exception as exc:
            return rejected_broker_fill(order, str(exc))

    def _remember(self, fills: tuple[BrokerFill, ...]) -> None:
        for fill in fills:
            self._recorded[fill.idempotency_key] = fill


def _execution_result(
    run_id: str,
    stage: ExecutionStage,
    fills: tuple[BrokerFill, ...],
    provenance: Provenance,
) -> ExecutionResult:
    public_fills: tuple[Fill, ...] = tuple(fill_from_broker(fill) for fill in fills)
    return ExecutionResult(
        run_id=run_id,
        stage=stage,
        fills=public_fills,
        submitted=sum(fill.status != "rejected" for fill in fills),
        rejected=sum(fill.status == "rejected" for fill in fills),
        provenance=provenance,
    )
