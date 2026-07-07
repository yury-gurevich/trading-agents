"""Execution agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: execution
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed PMRun nodes and submit them through the broker from the graph.
External I/O: master HTTP endpoint (POST /ehlo); injected broker.
"""

from __future__ import annotations

from agents.execution.broker_factory import broker_from_settings
from agents.execution.poll import execute_pm_node, find_pending
from agents.execution.settings import ExecutionSettings
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for PMRun → submit → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "execution", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = ExecutionSettings()
    broker = broker_from_settings(settings)
    work_loop(
        lambda: find_pending(graph),
        lambda node: execute_pm_node(
            node, graph=graph, broker=broker, settings=settings
        ),
        poll_interval=int(os.environ.get("EXECUTION_POLL_INTERVAL", "60")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
