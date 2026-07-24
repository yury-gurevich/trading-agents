"""Monitor per-position decision.

Agent: monitor
Role: observe one open Position against its stop and persist check/fault evidence.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.domain.exit_rules import evaluate_position
from agents.monitor.domain.positions import exit_position
from agents.monitor.store import write_check
from kernel import AgentFault
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, Node


def evaluate_one(
    graph: GraphStore,
    sink: FaultSink,
    monitor_run_id: str,
    position: Node,
    current_price_cents: int,
) -> bool:
    """Evaluate one open position; return whether its stop is breached."""
    ticker = str(position.props["ticker"])
    observation, trigger = evaluate_position(
        exit_position(position), current_price_cents
    )
    breached = observation == "stop_breached"
    write_check(
        graph,
        monitor_run_id=monitor_run_id,
        position=position,
        observation=observation,
        trigger=trigger,
        current_price_cents=current_price_cents,
    )
    if breached:
        _fault_sink(graph, sink).submit(
            AgentFault(
                source_agent="monitor",
                source_module="agents.monitor.decide",
                capability="check_positions",
                error_type="StopBreached",
                message=f"stop breached on {ticker}, still held",
            )
        )
    return breached


def _fault_sink(graph: GraphStore, sink: FaultSink) -> FaultSink:
    if isinstance(sink, GraphFaultSink):
        return sink
    return GraphFaultSink(graph, sink)
