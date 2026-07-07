"""Supervisor agent entrypoint — serve capabilities over serve_loop (S98).

Agent: supervisor
Role: EHLO to master, verify the signed ACTIVATE, bind the supervisor's capabilities
      to a bus, then serve its inbox forever (serve_loop) instead of idling. The real
      transport is selected from env, so local runs keep the empty inbox and
      distributed containers use Service Bus.
External I/O: master HTTP endpoint (POST /ehlo).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor.agent import SupervisorAgent
from kernel import InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.serve_loop import serve_loop
from kernel.serve_transport import consumer_from_env

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus


def build_served_bus(graph: GraphStore) -> MessageBus:
    """Bind the supervisor's capabilities to a fresh bus; return it ready to serve.

    Separated from main() so a test can bind, submit a request to a consumer, and
    serve_once without a live master or transport.
    """
    bus = InProcessBus()
    SupervisorAgent(bus, graph=graph).bind()
    return bus


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → bind supervisor capabilities → serve the inbox forever."""
    import os

    from kernel.graph_env import build_graph_from_env

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "supervisor", public_key_pem=pubkey)

    graph = build_graph_from_env()
    bus = build_served_bus(graph)
    serve_loop(consumer_from_env("supervisor", graph), bus)


if __name__ == "__main__":  # pragma: no cover
    main()
