"""Portfolio manager agent entrypoint — graph-pull work loop (DL-08 / DL-08b).

Agent: portfolio_manager
Role: EHLO to master, verify the signed ACTIVATE, then poll the graph for
      unprocessed AnalystRun nodes and size+risk-check them from the graph.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from agents.portfolio_manager.poll import evaluate_analyst_node, find_pending
from agents.portfolio_manager.settings import PortfolioManagerSettings
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.graph_env import build_graph_from_env
from kernel.work_loop import work_loop


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for AnalystRun → evaluate → repeat."""
    import os

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "portfolio_manager", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = PortfolioManagerSettings()
    work_loop(
        lambda: find_pending(graph),
        lambda node: evaluate_analyst_node(node, graph=graph, settings=settings),
        poll_interval=int(os.environ.get("PM_POLL_INTERVAL", "60")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
