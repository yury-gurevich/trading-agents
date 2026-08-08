"""Deliberator runtime adapter tests.

Agent: deliberator
Role: cover non-live manager, peer transport, settings, and store branches.
External I/O: none.
"""

from __future__ import annotations

import pytest

import agents.deliberator.entrypoint as entrypoint
from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient, ServiceBusPeerClient
from agents.deliberator.poll import _debate
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import write_deliberation_run
from contracts.common import Explanation, Provenance
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
    VerdictReply,
)
from contracts.portfolio_manager import OrderIntentSet
from kernel import AzureServiceBusSettings, FakeLLMClient, InMemoryGraphStore


class _NoKeyPeer:
    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        del recipient
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text="no ledger key",
            ),
        )


class _NoKeyManager:
    def verdict(self, request: object) -> VerdictReply:
        del request
        return VerdictReply(request_id="judge", ruling="uphold", rationale="no key")


def _order_set(run_id: str = "pm-1") -> OrderIntentSet:
    return OrderIntentSet(
        run_id=run_id,
        approved=(),
        rejected=(),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id=run_id, source_agent="portfolio_manager"),
    )


def _turn_request(role: str = "defender") -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id="turn-1",
        proposition=DebateProposition(decision="buy AAPL", context="ctx"),
        role=role,  # type: ignore[arg-type]
        round_number=1,
    )


def test_agent_rejects_wrong_peer_role() -> None:
    graph = InMemoryGraphStore()
    agent = DeliberatorAgent(
        entrypoint.InProcessBus(),
        graph=graph,
        settings=DeliberatorSettings(
            role="proponent", instance_name="deliberator-proponent"
        ),
    )

    with pytest.raises(ValueError, match="cannot serve challenger"):
        agent.debate_turn(_turn_request("challenger"))


def test_settings_manager_role_has_no_peer_role() -> None:
    settings = DeliberatorSettings(role="manager")

    assert settings.peer_role is None


def test_debate_can_return_without_llm_call_keys() -> None:
    review = _debate(
        "pm-1",
        "AAPL",
        DebateProposition(decision="buy AAPL", context="ctx"),
        _NoKeyManager(),  # type: ignore[arg-type]
        _NoKeyPeer(),
        DeliberatorSettings(max_rounds=1),
    )

    assert review.llm_call_keys == ()
    assert review.verdict == "uphold"


def test_store_reuses_existing_run_and_ignores_missing_llm_key() -> None:
    graph = InMemoryGraphStore()
    order_set = _order_set()
    pm_node = graph.merge_node("PMRun", "pm-1", {"order_intent_set": {}})
    graph.merge_node("LLMCall", "existing-call", {})

    first = write_deliberation_run(
        graph,
        pm_node,
        order_set=order_set,
        verdicts={},
        vetoed_tickers=[],
        debates={},
        narrative="none",
        transcript=[],
        role_models={},
        max_rounds=1,
        real_debate_count=0,
        failed_open_count=0,
        failed_open_tickers=[],
        failed_open_reason="",
        llm_call_keys=["existing-call", "missing-call"],
    )
    second = write_deliberation_run(
        graph,
        pm_node,
        order_set=order_set,
        verdicts={},
        vetoed_tickers=[],
        debates={},
        narrative="none",
        transcript=[],
        role_models={},
        max_rounds=1,
        real_debate_count=0,
        failed_open_count=0,
        failed_open_tickers=[],
        failed_open_reason="",
        llm_call_keys=[],
    )

    assert second is first
    assert len(graph.list_nodes("DeliberationRun")) == 1


def test_entrypoint_builders_choose_local_and_servicebus_peers(monkeypatch) -> None:
    graph = InMemoryGraphStore()
    entrypoint.build_served_bus(graph)
    entrypoint.build_served_bus(
        graph,
        DeliberatorSettings(role="proponent", instance_name="deliberator-proponent"),
    )
    monkeypatch.setattr(
        entrypoint,
        "AzureServiceBusSettings",
        lambda: AzureServiceBusSettings(
            connection_string=None, connection_strings_json=None
        ),
    )
    manager, peer = entrypoint.build_manager(
        graph,
        DeliberatorSettings(role="manager", instance_name="deliberator-manager"),
        llm=FakeLLMClient({}),
    )
    assert isinstance(manager, DeliberatorAgent)
    assert isinstance(peer, BusPeerClient)

    monkeypatch.setattr(
        entrypoint,
        "AzureServiceBusSettings",
        lambda: AzureServiceBusSettings(
            connection_string="Endpoint=sb://example/;SharedAccessKeyName=n;SharedAccessKey=k"
        ),
    )
    _, servicebus_peer = entrypoint.build_manager(
        graph,
        DeliberatorSettings(role="manager", instance_name="deliberator-manager"),
        llm=FakeLLMClient({}),
    )
    assert isinstance(servicebus_peer, ServiceBusPeerClient)
