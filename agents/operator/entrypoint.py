"""Operator agent entrypoint — serve capabilities over serve_loop (S98).

Agent: operator
Role: EHLO to master, verify the signed ACTIVATE, bind the operator's capabilities to
      a bus, then serve its inbox forever (serve_loop) instead of idling. The real
      transport inbox arrives in S100; until then the inbox is a LocalRequestConsumer,
      so a standalone container is serve-ready (idle on an empty inbox). Real LLM-client
      injection lands when the operator actively serves over the live transport (S100);
      today it binds with the agent's default client.
External I/O: master HTTP endpoint (POST /ehlo); LLM provider when it serves (S100).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.operator.agent import OperatorAgent
from kernel import InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.serve_loop import LocalRequestConsumer, serve_loop

if TYPE_CHECKING:
    from kernel import GraphStore, MessageBus


def build_served_bus(graph: GraphStore) -> MessageBus:
    """Bind the operator's capabilities to a fresh bus; return it ready to serve.

    Separated from main() so a test can bind, submit a request to a consumer, and
    serve_once without a live master or transport.
    """
    bus = InProcessBus()
    OperatorAgent(bus, graph=graph).bind()
    return bus


def main() -> None:  # pragma: no cover
    """EHLO → ACTIVATE → bind operator capabilities → serve the inbox forever."""
    import os

    from kernel.graph_env import build_graph_from_env

    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, "operator", public_key_pem=pubkey)

    bus = build_served_bus(build_graph_from_env())
    serve_loop(LocalRequestConsumer(), bus)


if __name__ == "__main__":  # pragma: no cover
    main()
