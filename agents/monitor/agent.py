"""Monitor agent implementation.

Agent: monitor
Role: open filled positions, observe stops, and publish
      monitor.decisions.ready claim-check events on execution.fills.ready.
External I/O: none; provider is reached only over the message bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents.monitor.provider_client import latest_close_cents
from agents.monitor.pubsub import on_fills_ready
from agents.monitor.run import evaluate_and_write, open_run_positions
from agents.monitor.settings import MonitorSettings
from agents.monitor.store import fills_for_run, is_open_position
from contracts.common import Explanation
from contracts.monitor import (
    CONTRACT,
    CloseDecisionSet,
    MonitorRequest,
)
from kernel import (
    AgentBase,
    CollectingFaultSink,
    FaultSink,
    GraphStore,
)

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

    def bind(self) -> None:
        """Register RPC handlers and subscribe to execution.fills.ready."""
        super().bind()
        self.bus.subscribe("execution.fills.ready", self._on_fills_ready)

    def _on_fills_ready(self, event: dict[str, Any]) -> None:
        on_fills_ready(self.bus, self._graph, self._check_positions, event)

    def _check_positions(self, request: BaseModel) -> CloseDecisionSet:
        monitor_request = MonitorRequest.model_validate(request)
        positions = open_run_positions(
            self._graph, self._settings, self.sink, source_run_id=monitor_request.run_id
        )
        prices = latest_close_cents(
            self.bus,
            self.sink,
            tickers=tuple(str(item.props["ticker"]) for item in positions),
            lookback_days=self._settings.price_lookback_days,
        )
        return evaluate_and_write(
            self._graph,
            self.sink,
            source_run_id=monitor_request.run_id,
            positions=positions,
            prices=prices,
        )

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
                "Monitor has not surfaced a stop breach for them in this check."
            ),
            evidence_refs=("contracts.stop_rule",),
        )

    def _positions_for_run(self, run_id: str) -> tuple[Node, ...]:
        positions: list[Node] = []
        for fill in fills_for_run(self._graph, run_id):
            positions.extend(
                self._graph.descendants(fill, max_depth=1, edge_types={"OPENS"})
            )
        return tuple(positions)
