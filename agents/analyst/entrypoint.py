"""Analyst agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: analyst
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed ScanRun nodes and score them from the graph.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from agents.analyst.poll import analyze_scan_node, find_pending
from agents.analyst.settings import AnalystSettings
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for ScanRun → analyze → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "analyst", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = AnalystSettings()
    work_loop(
        lambda: find_pending(graph),
        lambda node: analyze_scan_node(node, graph=graph, settings=settings),
        poll_interval=int(os.environ.get("ANALYST_POLL_INTERVAL", "60")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
