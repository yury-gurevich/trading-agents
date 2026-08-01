"""Compatibility adapter for the fleet-native deliberator agent.

Agent: orchestration
Role: keep local_pipeline's opt-in veto call working through deliberator instances.
External I/O: none directly; injected LLMClient owns model I/O.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import (
    DELIBERATED_EDGE as DELIBERATED_EDGE,
)
from agents.deliberator.store import (
    DELIBERATION_RUN_LABEL as DELIBERATION_RUN_LABEL,
)
from agents.deliberator.store import find_pending as find_pending
from kernel import InProcessBus

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, LLMClient, Node


def deliberate_pm_node(
    node: Node,
    *,
    graph: GraphStore,
    llm: LLMClient,
    judge_llm: LLMClient | None = None,
    max_rounds: int = 1,
    sink: FaultSink | None = None,
) -> None:
    """Review one PMRun through local deliberator instances for local_pipeline."""
    bus = InProcessBus()
    proponent = _peer(bus, graph, llm, role="proponent", max_rounds=max_rounds)
    opponent = _peer(bus, graph, llm, role="opponent", max_rounds=max_rounds)
    proponent.bind()
    opponent.bind()
    settings = DeliberatorSettings(
        role="manager",
        instance_name="deliberator-manager",
        max_rounds=max_rounds,
    )
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        llm=judge_llm if judge_llm is not None else llm,
        settings=settings,
    )
    review_pm_node(
        node,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=settings.identity),
        settings=settings,
        sink=sink,
    )


def _peer(
    bus: InProcessBus,
    graph: GraphStore,
    llm: LLMClient,
    *,
    role: str,
    max_rounds: int,
) -> DeliberatorAgent:
    settings = DeliberatorSettings(
        role=role,  # type: ignore[arg-type]
        instance_name=f"deliberator-{role}",
        max_rounds=max_rounds,
    )
    return DeliberatorAgent(bus, graph=graph, llm=llm, settings=settings)


__all__ = [
    "DELIBERATED_EDGE",
    "DELIBERATION_RUN_LABEL",
    "deliberate_pm_node",
    "find_pending",
]
