"""Provider agent entrypoint — graph-ingestor bootstrap.

Agent: provider
Role: EHLO to master, verify the signed ACTIVATE (creds injected into env),
      build the composite data source and graph store, then run the ingest loop.
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
    """EHLO → ACTIVATE (injects API keys into env) → build agent → ingest loop."""
    import os

    from agents.provider.ingest import ingest_loop, universe_from_env

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "provider", public_key_pem=pubkey)

    graph = build_graph_from_env()
    settings = ProviderSettings()
    agent = build_agent(settings, graph)
    ingest_loop(agent, universe_from_env())


if __name__ == "__main__":  # pragma: no cover
    main()
