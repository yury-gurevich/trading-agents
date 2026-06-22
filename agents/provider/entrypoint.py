"""Provider agent entrypoint — graph-pull work loop (DL-08).

Agent: provider
Role: EHLO to master, verify the signed ACTIVATE (creds injected into env),
      build the composite data source and graph store, then poll the graph for
      unprocessed RunRequest nodes and ingest their universe.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.provider.composite import market_source_from_settings
from agents.provider.settings import ProviderSettings
from kernel import InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.graph_env import build_graph_from_env

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from kernel.graph import GraphStore


def build_agent(settings: ProviderSettings, graph: GraphStore) -> ProviderAgent:
    """Assemble a ProviderAgent from settings and a graph store.

    Separated from main() so tests can call it without a live master.
    """
    from agents.provider import ProviderAgent

    source = market_source_from_settings(settings)
    bus = InProcessBus()
    return ProviderAgent(bus, graph=graph, source=source, settings=settings)


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → poll the graph for RunRequest → ingest → repeat."""
    import os

    from agents.provider.poll import find_pending, ingest_run_node
    from kernel.work_loop import work_loop

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "provider", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = ProviderSettings()
    agent = build_agent(settings, graph)
    work_loop(
        lambda: find_pending(graph),
        lambda node: ingest_run_node(node, agent=agent),
        poll_interval=int(os.environ.get("PROVIDER_POLL_INTERVAL", "60")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
