"""Deliberator manager peer-preflight tests.

Agent: deliberator
Role: prove Service Bus peer routing is checked before PMRun consumption.
External I/O: none.
"""

from __future__ import annotations

import json
from decimal import Decimal

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import ServiceBusPeerClient
from agents.deliberator.poll import find_pending, review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateTurnRecord, DebateTurnReply, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import (
    AzureServiceBusSettings,
    CollectingFaultSink,
    FakeLLMClient,
    GraphFaultSink,
    InMemoryGraphStore,
    InProcessBus,
    Node,
)
from kernel.serve_transport import request_topic


class _ResolvingPeerClient:
    def __init__(self, settings: AzureServiceBusSettings) -> None:
        self.settings = settings

    def preflight(self, recipients: tuple[str, ...]) -> None:
        for recipient in recipients:
            self.settings.connection_string_for_topic(request_topic(recipient))

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text=f"{recipient} addressed",
            ),
        )


def _settings_json(*topics: str) -> str:
    return json.dumps({topic: {"connection_string": f"{topic}-cs"} for topic in topics})


def _manager(graph: InMemoryGraphStore) -> DeliberatorAgent:
    return DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient(
            {"DECISION UNDER TEST": '{"ruling":"uphold","rationale":"ok"}'}
        ),
        settings=DeliberatorSettings(
            role="manager", instance_name="deliberator-manager"
        ),
    )


def _pm_node(graph: InMemoryGraphStore, run_id: str = "pm-1") -> Node:
    intent = OrderIntent(
        ticker="AAPL",
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="pm approved"),
    )
    order_set = OrderIntentSet(
        run_id=run_id,
        approved=(intent,),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id=run_id, source_agent="portfolio_manager"),
    )
    return graph.merge_node(
        "PMRun",
        run_id,
        {"order_intent_set": order_set.model_dump(mode="json")},
    )


def _sink(graph: InMemoryGraphStore) -> GraphFaultSink:
    return GraphFaultSink(graph, CollectingFaultSink())


def test_unreachable_peer_preflight_leaves_pmrun_unconsumed() -> None:
    """B1 DLIB-NEV-06: peer config failure faults before any clean veto record."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph)
    sink = _sink(graph)
    peer = _ResolvingPeerClient(
        AzureServiceBusSettings(
            _env_file=None,
            connection_string="manager-primary",
            connection_strings_json=_settings_json("deliberator-manager.requests"),
        )
    )

    review_pm_node(
        pm,
        graph=graph,
        manager=_manager(graph),
        peer_client=peer,
        settings=DeliberatorSettings(role="manager"),
        sink=sink,
    )

    assert graph.list_nodes("DeliberationRun") == ()
    assert [node.key for node in find_pending(graph)] == ["pm-1"]
    (fault,) = graph.list_nodes("Fault")
    assert fault.props["error_type"] == "BusConfigError"
    assert fault.props["capability"] == "peer_preflight"
    assert "deliberator-proponent.requests" in fault.props["message"]


def test_healthy_peer_preflight_still_records_real_debate() -> None:
    """B2 DLIB-OUT-01 / DLIB-NEV-06: resolvable peers do not disable the agent."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph)
    peer = _ResolvingPeerClient(
        AzureServiceBusSettings(
            _env_file=None,
            connection_string="manager-primary",
            connection_strings_json=_settings_json(
                "deliberator-proponent.requests",
                "deliberator-opponent.requests",
            ),
        )
    )

    review_pm_node(
        pm,
        graph=graph,
        manager=_manager(graph),
        peer_client=peer,
        settings=DeliberatorSettings(role="manager", max_rounds=1),
        sink=_sink(graph),
    )

    (run,) = graph.list_nodes("DeliberationRun")
    assert run.props["real_debate_count"] == 1
    assert run.props["failed_open_count"] == 0
    assert graph.list_nodes("Fault") == ()


def test_one_bad_peer_preflight_records_no_half_debate() -> None:
    """B3 DLIB-NEV-06: one missing peer is inert and loud, not half-clean."""
    graph = InMemoryGraphStore()
    pm = _pm_node(graph)
    sink = _sink(graph)
    peer = _ResolvingPeerClient(
        AzureServiceBusSettings(
            _env_file=None,
            connection_string="manager-primary",
            connection_strings_json=_settings_json("deliberator-proponent.requests"),
        )
    )

    review_pm_node(
        pm,
        graph=graph,
        manager=_manager(graph),
        peer_client=peer,
        settings=DeliberatorSettings(role="manager"),
        sink=sink,
    )

    assert graph.list_nodes("DeliberationRun") == ()
    assert [node.key for node in find_pending(graph)] == ["pm-1"]
    (fault,) = graph.list_nodes("Fault")
    assert "deliberator-opponent.requests" in fault.props["message"]


def test_servicebus_peer_client_preflight_resolves_peer_topics() -> None:
    """B2: live peer client resolves both peer request topics."""
    settings = AzureServiceBusSettings(
        _env_file=None,
        connection_string="manager-primary",
        connection_strings_json=_settings_json(
            "deliberator-proponent.requests",
            "deliberator-opponent.requests",
        ),
    )
    client = ServiceBusPeerClient(
        InMemoryGraphStore(), sender="deliberator-manager", settings=settings
    )

    client.preflight(("deliberator-proponent", "deliberator-opponent"))
