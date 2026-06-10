"""Monitor agent implementation.

Agent: monitor
Role: open filled positions, evaluate exits, and hand closes to execution.
External I/O: none; provider and execution are reached only over the message bus.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.monitor.domain.exit_rules import evaluate_position
from agents.monitor.domain.positions import exit_position, position_from_fill
from agents.monitor.execution_client import dispatch_closes
from agents.monitor.provider_client import latest_close_cents
from agents.monitor.result import decision_rationale, run_explanation
from agents.monitor.settings import MonitorSettings
from agents.monitor.store import (
    fills_for_run,
    is_open_position,
    open_position,
    open_positions,
    write_check,
    write_close_decision,
    write_monitor_run,
)
from contracts.common import Explanation
from contracts.monitor import (
    CONTRACT,
    CloseDecision,
    CloseDecisionSet,
    MonitorRequest,
)
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import MessageBus, Node


class MonitorAgent(AgentBase):
    """Monitor boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        settings: MonitorSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create a monitor with injected bus, graph, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._settings = settings or MonitorSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "check_positions": self._check_positions,
            "explain_hold": self._explain_hold,
        }

    def _check_positions(self, request: BaseModel) -> CloseDecisionSet:
        monitor_request = MonitorRequest.model_validate(request)
        monitor_run_id = f"monitor-run-{uuid.uuid4().hex}"
        positions = self._open_positions(monitor_request.run_id)
        positions_to_check = open_positions(self._graph, positions)
        prices = latest_close_cents(
            self.bus,
            self.sink,
            tickers=tuple(str(item.props["ticker"]) for item in positions_to_check),
            lookback_days=self._settings.price_lookback_days,
        )
        decisions = (
            ()
            if prices is None
            else self._evaluate_positions(monitor_run_id, positions_to_check, prices)
        )
        closes = tuple(item for item in decisions if item.decision == "close")
        provenance = write_monitor_run(
            self._graph,
            monitor_run_id=monitor_run_id,
            source_run_id=monitor_request.run_id,
            positions_checked=len(decisions),
            closes=len(closes),
            holds=len(decisions) - len(closes),
        )
        result = CloseDecisionSet(
            run_id=monitor_run_id,
            decisions=decisions,
            positions_checked=len(decisions),
            explanation=run_explanation(decisions),
            provenance=provenance,
        )
        dispatch_closes(self.bus, self.sink, result)
        return result

    def _explain_hold(self, request: BaseModel) -> Explanation:
        monitor_request = MonitorRequest.model_validate(request)
        held = [
            str(position.props["ticker"])
            for position in self._positions_for_run(monitor_request.run_id)
            if is_open_position(self._graph, position)
        ]
        if not held:
            return Explanation(
                summary=f"No open held positions found for {monitor_request.run_id}.",
                evidence_refs=("monitor.positions",),
            )
        return Explanation(
            summary=(
                f"Held {len(held)} open positions: {', '.join(sorted(held))}. "
                "No stop, target, or time exit has closed them yet."
            ),
            evidence_refs=("monitor.exit_rules",),
        )

    def _open_positions(self, run_id: str) -> tuple[Node, ...]:
        positions: list[Node] = []
        for fill in fills_for_run(self._graph, run_id):
            draft = position_from_fill(
                self._graph,
                run_id=run_id,
                fill=fill,
                default_stop_pct=self._settings.default_stop_pct,
                default_target_pct=self._settings.default_target_pct,
                default_horizon_days=self._settings.default_horizon_days,
            )
            if draft.degraded:
                self._record_degraded("position opened with fallback stop/target")
            positions.append(open_position(self._graph, draft, fill))
        return tuple(positions)

    def _positions_for_run(self, run_id: str) -> tuple[Node, ...]:
        positions: list[Node] = []
        for fill in fills_for_run(self._graph, run_id):
            positions.extend(
                self._graph.descendants(fill, max_depth=1, edge_types={"OPENS"})
            )
        return tuple(positions)

    def _evaluate_positions(
        self, monitor_run_id: str, positions: tuple[Node, ...], prices: dict[str, int]
    ) -> tuple[CloseDecision, ...]:
        decisions: list[CloseDecision] = []
        today = datetime.now(tz=UTC).date()
        for position in positions:
            ticker = str(position.props["ticker"])
            current_price_cents = prices.get(ticker)
            if current_price_cents is None:
                self._record_degraded(
                    f"provider returned no current price for {ticker}"
                )
                continue
            decision, trigger = evaluate_position(
                exit_position(position), current_price_cents, today
            )
            rationale = decision_rationale(ticker, decision, trigger)
            write_check(
                self._graph,
                monitor_run_id=monitor_run_id,
                position=position,
                decision=decision,
                trigger=trigger,
                current_price_cents=current_price_cents,
            )
            close = CloseDecision(
                ticker=ticker,
                position_id=position.key,
                decision=decision,
                trigger=trigger,
                rationale=rationale,
            )
            if decision == "close":
                write_close_decision(
                    self._graph,
                    monitor_run_id=monitor_run_id,
                    position=position,
                    decision=decision,
                    trigger=trigger,
                    rationale=rationale,
                )
            decisions.append(close)
        return tuple(decisions)

    def _record_degraded(self, message: str) -> None:
        with fault_boundary(
            self.sink,
            agent="monitor",
            module="agents.monitor.agent",
            capability="check_positions",
            reraise=False,
        ):
            raise RuntimeError(message)
