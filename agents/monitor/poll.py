"""Monitor graph-poll work source (DL-08 / DL-08b).

Agent: monitor
Role: find ExecutionRun nodes the monitor has not processed yet and evaluate the PM
      run's positions straight from the graph — reading fills via the PMRun lineage and
      current prices from the same-cycle MarketData (no live provider bus RPC).
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.provider_client import _latest_cents
from agents.monitor.run import evaluate_and_write, open_run_positions
from agents.monitor.settings import MonitorSettings
from contracts.provider import MarketData
from kernel import CollectingFaultSink
from kernel.fault_graph import GraphFaultSink

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, Node

EXECUTION_RUN_LABEL = "ExecutionRun"
MONITORED_EDGE = "MONITORED_BY"
_EXECUTED_EDGE = "EXECUTED_BY"
_EVALUATED_EDGE = "EVALUATED_BY"
_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return ExecutionRun nodes with no downstream MonitorRun (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(EXECUTION_RUN_LABEL):
        monitored = list(
            graph.descendants(node, max_depth=1, edge_types={MONITORED_EDGE})
        )
        if not monitored:
            pending.append(node)
    return pending


def monitor_pm_node(
    node: Node,
    *,
    graph: GraphStore,
    settings: MonitorSettings | None = None,
    sink: FaultSink | None = None,
) -> None:
    """Monitor one ExecutionRun's positions from the graph; link the MonitorRun back."""
    settings = settings or MonitorSettings()
    sink = sink if sink is not None else GraphFaultSink(graph, CollectingFaultSink())
    pm_run = next(
        iter(graph.ancestors(node, max_depth=1, edge_types={_EXECUTED_EDGE})), None
    )
    assert pm_run is not None  # ExecutionRun is always linked from its PMRun.
    pm_run_id = pm_run.key
    position_source = str(pm_run.props.get("linked_from_key", pm_run_id))
    positions = open_run_positions(graph, settings, sink, source_run_id=position_source)
    prices = _prices_from_graph(graph, pm_run)
    result = evaluate_and_write(
        graph,
        sink,
        source_run_id=pm_run_id,
        positions=positions,
        prices=prices,
    )
    monitor_run = graph.get_node("MonitorRun", result.run_id)
    assert monitor_run is not None  # just written by evaluate_and_write.
    graph.add_edge(node, monitor_run, MONITORED_EDGE)


def _prices_from_graph(graph: GraphStore, pm_run: Node) -> dict[str, int] | None:
    market_node = _market_node(graph, pm_run)
    if market_node is None:
        return None
    return _latest_cents(MarketData.model_validate(market_node.props["snapshot"]))


def _market_node(graph: GraphStore, pm_run: Node) -> Node | None:
    # PM lineage: (analyst)-[EVALUATED_BY]->(pm), (scan)-[ANALYZED_BY]->(analyst),
    # (scan)-[DERIVED_FROM]->(market). Walk the two ancestor hops, then the descendant.
    node: Node = pm_run
    for edge in (_EVALUATED_EDGE, _ANALYZED_EDGE):
        found = next(iter(graph.ancestors(node, max_depth=1, edge_types={edge})), None)
        if found is None:
            return None
        node = found
    return next(
        iter(graph.descendants(node, max_depth=1, edge_types={_DERIVED_FROM})), None
    )
