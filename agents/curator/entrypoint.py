"""Curator agent entrypoint -- PRE_FLIGHT bootstrap and request serving.

Agent: curator
Role: EHLO to master, verify ACTIVATE, then serve request-triggered capabilities.
External I/O: master HTTP endpoint (POST /ehlo); graph store selected from env.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.curator.agent import CuratorAgent
from kernel import InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.serve_loop import LocalRequestConsumer, serve_loop

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus


def build_served_bus(graph: GraphStore) -> MessageBus:
    """Bind curator RPC capabilities onto a local served bus."""
    bus = InProcessBus()
    CuratorAgent(bus, graph=graph).bind()
    return bus


def main() -> None:  # pragma: no cover
    """Activate with master, then serve request-triggered curator RPCs."""
    import os

    from kernel.graph_env import build_graph_from_env

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "curator", public_key_pem=pubkey)
    bus = build_served_bus(build_graph_from_env())
    serve_loop(LocalRequestConsumer(), bus)


if __name__ == "__main__":  # pragma: no cover
    main()
