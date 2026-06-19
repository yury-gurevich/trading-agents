"""Daily-loop dispatcher — P14 trigger-emitter.

Agent: orchestration
Role: fire run.trigger, collect report.snapshot.ready via claim-check, write narratives,
      and record the run to the supervisor. The per-agent pipeline is entirely event-driven;
      the dispatcher does not sequence individual agent steps.
External I/O: optional provider source and broker ports injected at construction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contracts.reporter import RunSnapshot
from contracts.supervisor import DispatchRunRecord
from kernel import AgentFault, CollectingFaultSink, claim_check_read
from kernel.errors import fault_boundary
from orchestration import run_outcome as outcome
from orchestration.bindings import bind_paper_loop_agents
from orchestration.narratives import write_narratives
from orchestration.settings import OrchestratorSettings
from orchestration.steps import step_record_dispatch_run
from orchestration.trigger import RunResult, RunTrigger

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.sources import DataSource
    from agents.scanner.universe import UniverseSource
    from kernel import FaultSink, GraphStore, MessageBus


class Dispatcher:
    """P14 trigger-emitter dispatcher for one paper trading loop."""

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
        """Publish run.trigger and wait for report.snapshot.ready to close the loop."""
        active = outcome.active_trigger(trigger, self.settings.universe)
        snapshot_received: list[dict[str, Any]] = []
        self.bus.subscribe("report.snapshot.ready", snapshot_received.append)

        with fault_boundary(
            self.sink,
            agent="orchestration",
            module="orchestration.dispatcher",
            capability="execute_run",
            reraise=False,
        ) as capture:
            self.bus.publish(
                "run.trigger",
                {"run_id": active.run_id, "universe": active.universe},
            )

        if capture.fault is not None or not snapshot_received:
            result = RunResult(
                run_id=active.run_id,
                completed=False,
                snapshot=None,
                steps_completed=0,
                reason="run produced no final snapshot",
            )
            self._record_run(result, ("run.trigger",))
            return result

        node = claim_check_read(self.graph, snapshot_received[0])
        snapshot = RunSnapshot.model_validate(node.props["snapshot"])
        write_narratives(self.bus, self.graph, snapshot.run_id, self.sink)
        result = RunResult(
            run_id=active.run_id,
            completed=True,
            snapshot=snapshot,
            steps_completed=6,
        )
        self._record_run(result, ("run.trigger",))
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
