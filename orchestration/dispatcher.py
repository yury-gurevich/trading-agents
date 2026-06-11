"""Daily-loop dispatcher.

Agent: orchestration
Role: bind the paper-loop agents and route one run through the bus.
External I/O: optional provider source and broker ports injected at construction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.supervisor import DispatchRunRecord
from kernel import AgentFault, CollectingFaultSink
from orchestration import run_outcome as outcome
from orchestration.bindings import bind_paper_loop_agents
from orchestration.narratives import write_narratives
from orchestration.settings import OrchestratorSettings
from orchestration.steps import (
    step_analyze,
    step_check_positions,
    step_evaluate,
    step_record_dispatch_run,
    step_report,
    step_scan,
    step_submit,
)
from orchestration.trigger import RunResult, RunTrigger

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.sources import DataSource
    from agents.scanner.universe import UniverseSource
    from kernel import FaultSink, GraphStore, MessageBus


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
        """Bind all paper-loop agents to the injected bus."""
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
        active = outcome.active_trigger(trigger, self.settings.universe)
        steps: list[str] = []
        candidates = step_scan(self.bus, active, self.sink)
        steps.append("scan")
        if candidates is None:
            return self._finish(
                outcome.stopped(active.run_id, 0, outcome.REASON_SCAN_EMPTY), steps
            )
        recommendations = step_analyze(self.bus, candidates, self.sink)
        steps.append("analyze")
        if recommendations is None:
            return self._finish(
                outcome.stopped(active.run_id, 1, outcome.REASON_ANALYSIS_EMPTY), steps
            )
        orders = step_evaluate(self.bus, recommendations, self.sink)
        steps.append("evaluate")
        if orders is None:
            return self._finish(
                outcome.stopped(active.run_id, 2, outcome.REASON_NO_ORDERS), steps
            )
        execution = step_submit(self.bus, orders, self.sink)
        steps.append("submit")
        if execution is None:
            return self._finish(
                outcome.stopped(active.run_id, 3, outcome.REASON_NO_FILLS), steps
            )
        decisions = step_check_positions(self.bus, orders.run_id, self.sink)
        steps.append("check_positions")
        if decisions is None:
            return self._finish(
                outcome.stopped(active.run_id, 4, outcome.REASON_NO_MONITOR), steps
            )
        snapshot = step_report(self.bus, orders.run_id, self.sink)
        steps.append("report")
        if snapshot is None:
            return self._finish(
                outcome.stopped(active.run_id, 5, outcome.REASON_NO_REPORT), steps
            )
        if not write_narratives(self.bus, self.graph, orders.run_id, self.sink):
            steps.append("narrative")
            return self._finish(
                RunResult(
                    run_id=active.run_id,
                    completed=False,
                    snapshot=snapshot,
                    steps_completed=6,
                    reason=outcome.REASON_NO_NARRATIVE,
                ),
                steps,
            )
        steps.append("narrative")
        return self._finish(
            RunResult(
                run_id=active.run_id,
                completed=True,
                snapshot=snapshot,
                steps_completed=7,
            ),
            steps,
        )

    def _finish(self, result: RunResult, steps: list[str]) -> RunResult:
        self._record_run(result, tuple(steps))
        return result

    def _record_run(self, result: RunResult, steps: tuple[str, ...]) -> None:
        faults = tuple(
            fault
            for fault in getattr(self.sink, "faults", ())
            if isinstance(fault, AgentFault)
        )
        step_record_dispatch_run(
            self.bus,
            DispatchRunRecord(
                run_id=result.run_id,
                steps_attempted=steps,
                completed=result.completed,
                reason=result.reason,
                faults=faults,
            ),
            self.sink,
        )
