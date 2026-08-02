"""Monitor agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: monitor
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed ExecutionRun nodes and evaluate their positions from the graph.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from agents.monitor.poll import find_pending_work, process_work_item
from agents.monitor.settings import MonitorSettings
from kernel import CollectingFaultSink
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.fault_graph import GraphFaultSink
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop
from kernel.work_loop_policy import poll_interval_from_env


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for ExecutionRun → monitor → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "monitor", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = MonitorSettings()
    fault_sink = GraphFaultSink(graph, CollectingFaultSink())
    work_loop(
        lambda: find_pending_work(graph),
        lambda item: process_work_item(
            item, graph=graph, settings=settings, sink=fault_sink
        ),
        poll_interval=poll_interval_from_env("MONITOR_POLL_INTERVAL"),
        graph=graph,
        agent="monitor",
        flush_faults=fault_sink.flush,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
