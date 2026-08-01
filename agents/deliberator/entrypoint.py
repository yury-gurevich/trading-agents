"""Deliberator agent entrypoint.

Agent: deliberator
Role: activate one deliberator role, then graph-pull as manager or serve as peer.
External I/O: master HTTP endpoint, graph store, Service Bus, Anthropic API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient, ServiceBusPeerClient
from agents.deliberator.settings import DeliberatorSettings
from kernel import AzureServiceBusSettings, InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.serve_loop import serve_loop
from kernel.serve_transport import consumer_from_env

if TYPE_CHECKING:
    from agents.deliberator.peer_client import PeerClient
    from kernel import GraphStore, LLMClient, MessageBus


def build_served_bus(
    graph: GraphStore, settings: DeliberatorSettings | None = None
) -> MessageBus:
    """Bind a served deliberator peer role onto a fresh bus."""
    resolved = settings if settings is not None else DeliberatorSettings()
    bus = InProcessBus()
    DeliberatorAgent(bus, graph=graph, settings=resolved).bind()
    return bus


def build_manager(
    graph: GraphStore,
    settings: DeliberatorSettings | None = None,
    llm: LLMClient | None = None,
) -> tuple[DeliberatorAgent, PeerClient]:
    """Build the manager and its production peer-client port."""
    resolved = settings if settings is not None else DeliberatorSettings()
    bus = InProcessBus()
    manager = DeliberatorAgent(bus, graph=graph, llm=llm, settings=resolved)
    sb_settings = AzureServiceBusSettings()
    if (
        sb_settings.connection_string is None
        and sb_settings.connection_strings_json is None
    ):
        return manager, BusPeerClient(bus, sender=resolved.identity)
    return manager, ServiceBusPeerClient(
        graph,
        sender=resolved.identity,
        settings=sb_settings,
        timeout_seconds=resolved.request_timeout_seconds,
    )


def main() -> None:  # pragma: no cover
    """EHLO, build role, then run manager or served-peer loop forever."""
    import os

    from agents.deliberator.llm_anthropic import AnthropicLLMClient
    from agents.deliberator.poll import find_pending, review_pm_node
    from kernel.graph_env import build_graph_from_env
    from kernel.work_loop import work_loop

    settings = DeliberatorSettings()
    master_url = os.environ.get("MASTER_URL", "http://master:8000")
    pubkey = master_public_key_from_env()
    activate_agent(master_url, settings.identity, public_key_pem=pubkey)
    graph = build_graph_from_env()
    llm = AnthropicLLMClient(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        model=settings.model_for_role(settings.peer_role or "judge"),
        max_tokens=settings.max_tokens,
        effort=settings.effort,
    )
    if settings.role == "manager":
        manager, peer_client = build_manager(graph, settings, llm=llm)
        work_loop(
            lambda: find_pending(graph),
            lambda node: review_pm_node(
                node,
                graph=graph,
                manager=manager,
                peer_client=peer_client,
                settings=settings,
            ),
            poll_interval=settings.poll_interval_seconds,
        )
        return
    bus = InProcessBus()
    DeliberatorAgent(bus, graph=graph, llm=llm, settings=settings).bind()
    serve_loop(consumer_from_env(settings.identity, graph), bus)


if __name__ == "__main__":  # pragma: no cover
    main()
