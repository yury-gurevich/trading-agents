"""Reporter agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: reporter
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed MonitorRun nodes and build their snapshot from the graph.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from agents.reporter.poll import find_pending, report_monitor_node
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for MonitorRun → report → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "reporter", public_key_pem=pubkey)

    graph = build_graph_from_env()
    work_loop(
        lambda: find_pending(graph),
        lambda node: report_monitor_node(node, graph=graph),
        poll_interval=int(os.environ.get("REPORTER_POLL_INTERVAL", "60")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
