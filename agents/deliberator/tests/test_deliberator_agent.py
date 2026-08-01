"""Deliberator agent tests.

Agent: deliberator
Role: prove the fleet-native manager/peer debate path and audit writes.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import find_pending, review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATED_EDGE, DELIBERATION_RUN_LABEL
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateProposition, DebateTurnReply, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import AgentMessage, FakeLLMClient, InMemoryGraphStore, InProcessBus, Node
from kernel.serve_loop import LocalRequestConsumer, serve_once

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'


class _FailingPeerClient:
    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        del recipient, request
        raise RuntimeError("peer unavailable")


def _settings(role: str, *, rounds: int = 2) -> DeliberatorSettings:
    return DeliberatorSettings(
        role=role,  # type: ignore[arg-type]
        instance_name=f"deliberator-{role}",
        max_rounds=rounds,
    )


def _orders(run_id: str = "pm-1") -> OrderIntentSet:
    intent = OrderIntent(
        ticker="AAPL",
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="pm approved"),
    )
    return OrderIntentSet(
        run_id=run_id,
        approved=(intent,),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id=run_id, source_agent="portfolio_manager"),
    )


def _pm_node(graph: InMemoryGraphStore, run_id: str = "pm-1") -> Node:
    order_set = _orders(run_id)
    return graph.merge_node(
        "PMRun",
        run_id,
        {"order_intent_set": order_set.model_dump(mode="json")},
    )


def test_peer_served_turn_writes_attributable_llm_call() -> None:
    """DL-80: proponent is a served peer, not an in-process prompt branch."""
    graph = InMemoryGraphStore()
    bus = InProcessBus()
    agent = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": "defend from evidence"}),
        settings=_settings("proponent", rounds=1),
    )
    agent.bind()
    request = DebateTurnRequest(
        request_id="turn-1",
        proposition=DebateProposition(decision="buy AAPL", context="ctx"),
        role="defender",
        round_number=1,
    )
    consumer = LocalRequestConsumer(
        [
            AgentMessage(
                sender="deliberator-manager",
                recipient="deliberator-proponent",
                message_type="request",
                capability="debate_turn",
                payload=request.model_dump(mode="json"),
            )
        ]
    )

    assert serve_once(consumer, bus) == 1

    reply = DebateTurnReply.model_validate(consumer.replies[0].payload)
    assert reply.turn.role == "defender"
    (call,) = graph.list_nodes("LLMCall")
    assert call.props["calling_agent"] == "deliberator-proponent"


def test_manager_reviews_pending_pmrun_with_two_peer_rounds_and_llm_costs() -> None:
    """DL-80 / ADR-0020: manager writes DeliberationRun and shared LLMCall costs."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph)
    bus = InProcessBus()
    proponent = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": "defense"}),
        settings=_settings("proponent"),
    )
    opponent = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": "challenge"}),
        settings=_settings("opponent"),
    )
    manager_settings = _settings("manager")
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=manager_settings,
    )
    proponent.bind()
    opponent.bind()

    assert [node.key for node in find_pending(graph)] == ["pm-1"]
    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=manager_settings.identity),
        settings=manager_settings,
    )

    assert find_pending(graph) == []
    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    assert run.props["vetoed_tickers"] == ()
    assert len(run.props["transcript"]) == 4
    assert run.props["role_models"]["judge"] == "claude-opus-5"
    callers = {node.props["calling_agent"] for node in graph.list_nodes("LLMCall")}
    assert callers == {
        "deliberator-manager",
        "deliberator-proponent",
        "deliberator-opponent",
    }
    linked = list(graph.descendants(pm, max_depth=1, edge_types={DELIBERATED_EDGE}))
    assert linked == [run]


def test_manager_fail_open_records_visible_rationale() -> None:
    """DL-80: peer failure records fail-open and never produces a clean veto."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph, "pm-fail")
    bus = InProcessBus()
    settings = _settings("manager")
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=settings,
    )

    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=_FailingPeerClient(),
        settings=settings,
    )

    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    assert run.props["vetoed_tickers"] == ()
    assert "fail-open" in run.props["narrative"]
