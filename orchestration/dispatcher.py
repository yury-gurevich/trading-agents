"""Daily-loop dispatcher.

Agent: orchestration
Role: bind the seven paper-loop agents and route one run through the bus.
External I/O: optional provider source and broker ports injected at construction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel import CollectingFaultSink
from orchestration.bindings import bind_paper_loop_agents
from orchestration.settings import OrchestratorSettings
from orchestration.steps import (
    step_analyze,
    step_check_positions,
    step_evaluate,
    step_narrative,
    step_report,
    step_scan,
    step_submit,
)
from orchestration.trigger import RunResult, RunTrigger

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.sources import DataSource
    from agents.scanner.universe import UniverseSource
    from kernel import FaultSink, GraphStore, MessageBus, Node

REASON_SCAN_EMPTY = "scan produced no candidates"
REASON_ANALYSIS_EMPTY = "analysis produced no recommendations"
REASON_NO_ORDERS = "portfolio manager approved no orders"
REASON_NO_FILLS = "execution produced no submitted fills"
REASON_NO_MONITOR = "monitor produced no position decisions"
REASON_NO_REPORT = "reporter produced no snapshot"
REASON_NO_NARRATIVE = "reporter produced no trade narratives"


class Dispatcher:
    """P4 dispatcher for one paper trading loop."""

    def __init__(
        self,
        bus: MessageBus,
        graph: GraphStore,
        *,
        settings: OrchestratorSettings | None = None,
        source: DataSource | None = None,
        broker: Broker | None = None,
        universe_source: UniverseSource | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Bind all seven paper-loop agents to the injected bus."""
        self.bus = bus
        self.graph = graph
        self.settings = settings or OrchestratorSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        bind_paper_loop_agents(
            bus,
            graph=graph,
            settings=self.settings,
            source=source,
            broker=broker,
            universe_source=universe_source,
            sink=self.sink,
        )

    def execute_run(self, trigger: RunTrigger) -> RunResult:
        """Execute the daily paper loop and stop gracefully on the first empty step."""
        active = _active_trigger(trigger, self.settings.universe)
        candidates = step_scan(self.bus, active, self.sink)
        if candidates is None:
            return _stopped(active.run_id, 0, REASON_SCAN_EMPTY)
        recommendations = step_analyze(self.bus, candidates, self.sink)
        if recommendations is None:
            return _stopped(active.run_id, 1, REASON_ANALYSIS_EMPTY)
        orders = step_evaluate(self.bus, recommendations, self.sink)
        if orders is None:
            return _stopped(active.run_id, 2, REASON_NO_ORDERS)
        execution = step_submit(self.bus, orders, self.sink)
        if execution is None:
            return _stopped(active.run_id, 3, REASON_NO_FILLS)
        decisions = step_check_positions(self.bus, orders.run_id, self.sink)
        if decisions is None:
            return _stopped(active.run_id, 4, REASON_NO_MONITOR)
        snapshot = step_report(self.bus, orders.run_id, self.sink)
        if snapshot is None:
            return _stopped(active.run_id, 5, REASON_NO_REPORT)
        if not self._write_narratives(orders.run_id):
            return RunResult(
                run_id=active.run_id,
                completed=False,
                snapshot=snapshot,
                steps_completed=6,
                reason=REASON_NO_NARRATIVE,
            )
        return RunResult(
            run_id=active.run_id,
            completed=True,
            snapshot=snapshot,
            steps_completed=6,
        )

    def _write_narratives(self, pm_run_id: str) -> bool:
        position_ids = _position_ids_for_run(self.graph, pm_run_id)
        stories = [
            step_narrative(self.bus, position_id, self.sink)
            for position_id in position_ids
        ]
        return bool(stories) and all(story is not None for story in stories)


def _active_trigger(trigger: RunTrigger, default_universe: str) -> RunTrigger:
    if trigger.universe:
        return trigger
    return trigger.model_copy(update={"universe": default_universe})


def _stopped(run_id: str, steps_completed: int, reason: str) -> RunResult:
    return RunResult(
        run_id=run_id,
        completed=False,
        snapshot=None,
        steps_completed=steps_completed,
        reason=reason,
    )


def _position_ids_for_run(graph: GraphStore, pm_run_id: str) -> tuple[str, ...]:
    pm_run = graph.get_node("PMRun", pm_run_id)
    if pm_run is None:
        return ()
    positions: dict[str, Node] = {}
    for order in graph.ancestors(pm_run, max_depth=1, edge_types={"EMITTED_BY"}):
        for fill in graph.ancestors(order, max_depth=1, edge_types={"EXECUTES"}):
            for position in graph.descendants(fill, max_depth=1, edge_types={"OPENS"}):
                positions[position.key] = position
    return tuple(positions)
