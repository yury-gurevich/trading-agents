"""A19-A20: a run names the models that answered each serving identity.

Agent: deliberator
Role: prove real review records and multi-replica model aggregation.
External I/O: none; in-process bus, canned clients and graph.
"""

from typing import Literal

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import review_pm_node
from agents.deliberator.review_record import role_models
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.test_deliberator_agent import _pm_node
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus


def test_a19_review_names_the_models_that_answered() -> None:
    """DLIB-OUT-02: mixed-vendor peer ledgers determine a real run's role_models."""
    graph, bus = InMemoryGraphStore(), InProcessBus()
    pm = _pm_node(graph)
    peers: tuple[tuple[Literal["proponent", "opponent"], str], ...] = (
        ("proponent", "anthropic"),
        ("opponent", "openai"),
    )
    for role, provider in peers:
        DeliberatorAgent(
            bus,
            graph=graph,
            llm=FakeLLMClient({"DECISION UNDER TEST": "evidence argument"}),
            settings=DeliberatorSettings(
                _env_file=None, role=role, llm_provider=provider, max_rounds=1
            ),
        ).bind()
    settings = DeliberatorSettings(
        _env_file=None, role="manager", llm_provider="openai", max_rounds=1
    )
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        settings=settings,
        llm=FakeLLMClient(
            {"DECISION UNDER TEST": '{"ruling":"uphold","rationale":"clears"}'}
        ),
    )
    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=settings.identity),
        settings=settings,
    )
    (run,) = graph.list_nodes("DeliberationRun")
    assert run.props["real_debate_count"] == 1
    assert run.props["failed_open_count"] == 0
    assert run.props["role_models"] == {
        "defender": "claude-opus-5",
        "challenger": "gpt-5.5",
        "judge": "gpt-5.5",
    }
    assert len(graph.list_nodes("LLMCall")) == 3


def test_a20_multiple_models_on_one_role_are_sorted_and_deduplicated() -> None:
    """DLIB-OUT-02: run-owned rows, serving identities and resolved fallbacks govern."""
    graph = InMemoryGraphStore()
    settings = DeliberatorSettings(
        _env_file=None, llm_provider="openai", proponent_identity="defender-replica"
    )
    for key, model in (("a", "gpt-5.5"), ("b", "claude-opus-5"), ("c", "gpt-5.5")):
        graph.merge_node(
            "LLMCall", key, {"calling_agent": "defender-replica", "model": model}
        )
    graph.merge_node(
        "LLMCall",
        "other-run",
        {"calling_agent": "defender-replica", "model": "gpt-outside-run"},
    )
    graph.merge_node("LLMCall", "bad-model", {"model": 1})
    graph.merge_node("LLMCall", "unrelated", {"model": "unrelated"})
    keys = ["a", "b", "c", "missing", "bad-model", "unrelated"]
    expected = {
        "defender": "claude-opus-5, gpt-5.5",
        "challenger": "gpt-5.5",
        "judge": "gpt-5.5",
    }
    assert role_models(settings, graph, keys) == expected
    assert role_models(settings, None, keys) == {
        "defender": "gpt-5.5",
        "challenger": "gpt-5.5",
        "judge": "gpt-5.5",
    }
