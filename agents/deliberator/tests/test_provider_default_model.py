"""A provider switch is one switch, and the audit record names what answered.

Agent: deliberator
Role: pin that an unset role model resolves the provider's own default, that an
      explicit setting still wins, and that the DeliberationRun records the
      resolved name rather than the sentinel or the other vendor's.
External I/O: none — the LLM is a fake and no client is constructed.

DL-100 measured the defect on the live fleet: `DELIBERATOR_LLM_PROVIDER=openai`
alone sent `claude-opus-5` to OpenAI, and `role_models` would have stamped that
Anthropic name on an order OpenAI reviewed — the provenance claim DL-99 exists to
protect, quietly false. Every assertion below that matters is made on the
**written node**, because a green settings object is what let this ship.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.llm_factory import (
    DEFAULT_MODEL,
    KEY_ENV,
    UnknownProviderError,
    default_model_for,
)
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus, Node

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'


def _settings(role: str, **over: str) -> DeliberatorSettings:
    return DeliberatorSettings(
        role=role,  # type: ignore[arg-type]
        instance_name=f"deliberator-{role}",
        max_rounds=1,
        **over,  # type: ignore[arg-type]
    )


def _pm_node(graph: InMemoryGraphStore) -> Node:
    intent = OrderIntent(
        ticker="AAPL",
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="pm approved"),
    )
    order_set = OrderIntentSet(
        run_id="pm-1",
        approved=(intent,),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-1", source_agent="portfolio_manager"),
    )
    return graph.merge_node(
        "PMRun", "pm-1", {"order_intent_set": order_set.model_dump(mode="json")}
    )


def _written_role_models(**over: str) -> dict[str, str]:
    """Run one review and return the role_models actually written to the graph."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph)
    bus = InProcessBus()
    for role, reply in (("proponent", "defense"), ("opponent", "challenge")):
        DeliberatorAgent(
            bus,
            graph=graph,
            llm=FakeLLMClient({"DECISION UNDER TEST": reply}),
            settings=_settings(role, **over),
        ).bind()
    manager_settings = _settings("manager", **over)
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=manager_settings,
    )
    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=manager_settings.identity),
        settings=manager_settings,
    )
    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    return dict(run.props["role_models"])


def test_the_provider_alone_switches_every_role_model() -> None:
    """DL-100: with only llm_provider set, the record names OpenAI's model."""
    assert _written_role_models(llm_provider="openai") == {
        "defender": "gpt-5.5",
        "challenger": "gpt-5.5",
        "judge": "gpt-5.5",
    }


def test_the_anthropic_path_is_not_quietly_repointed() -> None:
    """The fix must not change what an unconfigured deployment already does."""
    assert _written_role_models() == {
        "defender": "claude-opus-5",
        "challenger": "claude-opus-5",
        "judge": "claude-opus-5",
    }


def test_no_role_is_ever_recorded_as_the_empty_sentinel() -> None:
    """A role_models entry of "" is a worse audit record than a wrong one."""
    for provider in KEY_ENV:
        written = _written_role_models(llm_provider=provider)
        assert "" not in written.values()


@pytest.mark.parametrize("provider", sorted(KEY_ENV))
@pytest.mark.parametrize("role", ["defender", "challenger", "judge"])
def test_an_explicit_model_still_wins(provider: str, role: str) -> None:
    """An operator override outranks the provider default, every role."""
    settings = _settings("manager", llm_provider=provider, **{f"{role}_model": "x"})

    assert settings.model_for_role(role) == "x"  # type: ignore[arg-type]


def test_every_provider_that_has_a_key_has_a_default_model() -> None:
    """A third vendor cannot be half-added and resolve to nothing."""
    assert sorted(DEFAULT_MODEL) == sorted(KEY_ENV)


def test_an_unknown_provider_has_no_default_model() -> None:
    """Refusing beats resolving a model for a vendor that does not exist."""
    with pytest.raises(UnknownProviderError):
        default_model_for("gemini")
