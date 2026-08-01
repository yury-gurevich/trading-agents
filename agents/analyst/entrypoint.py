"""Analyst agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: analyst
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed ScanRun nodes and score them from the graph.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from agents.analyst.poll import analyze_scan_node, find_pending
from agents.analyst.settings import AnalystSettings
from kernel import CollectingFaultSink
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.fault_graph import GraphFaultSink
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop
from kernel.work_loop_policy import poll_interval_from_env


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for ScanRun → analyze → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "analyst", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = AnalystSettings()
    fault_sink = GraphFaultSink(graph, CollectingFaultSink())
    work_loop(
        lambda: find_pending(graph),
        lambda node: analyze_scan_node(
            node, graph=graph, settings=settings, sink=fault_sink
        ),
        poll_interval=poll_interval_from_env("ANALYST_POLL_INTERVAL"),
        graph=graph,
        agent="analyst",
        flush_faults=fault_sink.flush,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
