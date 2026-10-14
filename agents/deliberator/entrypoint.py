"""Deliberator agent entrypoint.

Agent: deliberator
Role: activate one deliberator role, then graph-pull as manager or serve as peer.
External I/O: master HTTP endpoint, graph store, Service Bus, the chosen LLM API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient, ServiceBusPeerClient
from agents.deliberator.settings import DeliberatorSettings
from kernel import AzureServiceBusSettings, CollectingFaultSink, InProcessBus
from kernel.bootstrap import activate_agent, master_public_key_from_env
from kernel.fault_graph import GraphFaultSink
from kernel.llm_factory import build_llm, key_env_var
from kernel.serve_loop import serve_loop
from kernel.serve_transport import consumer_from_env

PEER_SERVE_IDLE_SLEEP_SECONDS = 0

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.deliberator.peer_client import PeerClient
    from kernel import FaultSink, GraphStore, LLMClient, MessageBus


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
    sink: FaultSink | None = None,
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
        sink=sink,
    )


def activated_settings(
    settings: DeliberatorSettings,
    master_url: str,
    public_key_pem: str | None,
    activate: Callable[..., object] = activate_agent,
) -> DeliberatorSettings:
    """EHLO as this role, then re-read settings so the master's hand-over applies.

    The master names the role's vendor, model and effort in ACTIVATE's config,
    which lands in the process environment (DL-289); settings read before it
    would run the role on the image's defaults.
    """
    activate(master_url, settings.identity, public_key_pem=public_key_pem)
    return DeliberatorSettings()


def build_role_llm(
    settings: DeliberatorSettings, environ: Mapping[str, str]
) -> LLMClient:
    """Build the role's client on the vendor, model and effort it was handed."""
    return build_llm(
        settings.llm_provider,
        api_key=environ.get(key_env_var(settings.llm_provider)),
        model=settings.model_for_role(settings.peer_role or "judge"),
        max_tokens=settings.max_tokens,
        effort=settings.effort or None,
    )


def serve_peer(
    graph: GraphStore, settings: DeliberatorSettings, llm: LLMClient | None
) -> None:
    """Serve a peer without sleeping beyond the Service Bus receive wait."""
    bus = InProcessBus()
    DeliberatorAgent(bus, graph=graph, llm=llm, settings=settings).bind()
    serve_loop(
        consumer_from_env(settings.identity, graph),
        bus,
        poll_interval=PEER_SERVE_IDLE_SLEEP_SECONDS,
        sink=GraphFaultSink(graph, CollectingFaultSink()),
        graph=graph,
        agent=settings.identity,
    )


def main() -> None:  # pragma: no cover
    """EHLO, build role, then run manager or served-peer loop forever."""
    import os

    from agents.deliberator.poll import find_pending, review_pm_node
    from kernel.graph_env import build_graph_from_env
    from kernel.work_loop import work_loop

    settings = activated_settings(
        DeliberatorSettings(),
        os.environ.get("MASTER_URL", "http://master:8000"),
        master_public_key_from_env(),
    )
    graph = build_graph_from_env()
    llm = build_role_llm(settings, os.environ)
    if settings.role == "manager":
        fault_sink = GraphFaultSink(graph, CollectingFaultSink())
        manager, peer_client = build_manager(graph, settings, llm=llm, sink=fault_sink)
        work_loop(
            lambda: find_pending(graph),
            lambda node: review_pm_node(
                node,
                graph=graph,
                manager=manager,
                peer_client=peer_client,
                settings=settings,
                sink=fault_sink,
            ),
            poll_interval=settings.poll_interval_seconds,
            graph=graph,
            agent=settings.identity,
            flush_faults=fault_sink.flush,
        )
        return
    serve_peer(graph, settings, llm)


if __name__ == "__main__":  # pragma: no cover
    main()
