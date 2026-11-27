"""Test-lane debate — the three deliberator roles on one in-process bus.

Agent: orchestration
Role: wire the deliberator's manager and its two peers for a test-lane run (DL-328):
      the peers are bound on one ``InProcessBus`` and the manager reaches them through
      ``BusPeerClient``, where the fleet uses Service Bus; every role answers with a
      fake model, so a lane run makes no paid call.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import find_pending, review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from kernel import FakeLLMClient, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel import FaultSink, GraphStore, LLMClient

FAKE_JUDGE_RULING = (
    '{"ruling": "uphold", "rationale": "test lane: the fake judge upholds every order"}'
)
"""Every judge ruling in a lane run is this fake ``uphold``."""


@dataclass(frozen=True)
class DebateModels:
    """The model each deliberator role answers with."""

    proponent: LLMClient
    opponent: LLMClient
    judge: LLMClient


def fake_debate_models() -> DebateModels:
    """Return a fake model for each of the three roles."""
    return DebateModels(
        proponent=FakeLLMClient({"DECISION UNDER TEST": "test lane: defend"}),
        opponent=FakeLLMClient({"DECISION UNDER TEST": "test lane: challenge"}),
        judge=FakeLLMClient({"DECISION UNDER TEST": FAKE_JUDGE_RULING}),
    )


def debate_pair(
    graph: GraphStore, models: DebateModels, sink: FaultSink
) -> tuple[Callable[[], list[Any]], Callable[[Any], None]]:
    """Return the manager's work pair, its two peers bound beside it."""
    bus = InProcessBus()
    for role, llm in (("proponent", models.proponent), ("opponent", models.opponent)):
        DeliberatorAgent(bus, graph=graph, llm=llm, settings=_role(role)).bind()
    settings = _role("manager")
    manager = DeliberatorAgent(bus, graph=graph, llm=models.judge, settings=settings)
    process = partial(
        review_pm_node,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=settings.identity),
        settings=settings,
        sink=sink,
    )
    return partial(find_pending, graph), process


def _role(role: str) -> DeliberatorSettings:
    return DeliberatorSettings(
        role=role,  # type: ignore[arg-type]
        instance_name=f"deliberator-{role}",
    )
