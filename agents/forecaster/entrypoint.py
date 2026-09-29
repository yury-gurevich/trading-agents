"""Forecaster agent entrypoint — graph-pull work loop (DL-08 / DL-241 D9).

Agent: forecaster
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for current
      AnalystRun nodes: fire the deployed legs (the barrier claim only) at the
      forecaster's own capabilities, bound on a local bus, and run each run's
      settlement pass over the claims its bars decide (DL-243).
External I/O: master HTTP endpoint (POST /ehlo); graph store selected from env.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.agent import ForecasterAgent
from agents.forecaster.poll import DEPLOYED_CAPABILITIES
from agents.forecaster.work import find_pending_work, process_work_item
from kernel import CollectingFaultSink, InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.fault_graph import GraphFaultSink
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop
from kernel.work_loop_policy import poll_interval_from_env

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, MessageBus


def build_served_bus(graph: GraphStore, sink: FaultSink | None = None) -> MessageBus:
    """Bind the forecaster's capabilities onto a local bus."""
    bus = InProcessBus()
    ForecasterAgent(bus, graph=graph, sink=sink).bind()
    return bus


def main() -> None:
    """EHLO → ACTIVATE → poll for AnalystRun → forecast, then settle → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "forecaster", public_key_pem=pubkey)

    graph = build_graph_from_env()
    fault_sink = GraphFaultSink(graph, CollectingFaultSink())
    bus = build_served_bus(graph, fault_sink)
    work_loop(
        lambda: find_pending_work(graph, now=datetime.now(tz=UTC)),
        lambda item: process_work_item(
            item,
            graph=graph,
            bus=bus,
            capabilities=DEPLOYED_CAPABILITIES,
            sink=fault_sink,
        ),
        poll_interval=poll_interval_from_env("FORECASTER_POLL_INTERVAL"),
        graph=graph,
        agent="forecaster",
        flush_faults=fault_sink.flush,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
