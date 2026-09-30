"""The record keeps each turn's reading and the packet it read (S246 B5, B4).

Agent: deliberator
Role: prove a full manager review records every debater turn's guided reasoning
      or why it could not be read, and each order's decision and packet.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from agents.deliberator.tests.guided_fixtures import (
    EXPECTED_TEXT,
    REASONING,
    UNREADABLE,
    VALID,
    RecordingLLM,
)
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, InProcessBus
from kernel.deliberation_guided import GuidedReasoning

if TYPE_CHECKING:
    from contracts.deliberator import DebateTurnReply, DebateTurnRequest
    from kernel import Node

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'


class _Recording(BusPeerClient):
    """The real bus client, keeping every proposition it sent."""

    requests: list[DebateTurnRequest]

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        self.requests.append(request)
        return super().debate_turn(recipient, request)


def _review(peer_answer: str) -> tuple[Node, list[DebateTurnRequest]]:
    graph = InMemoryGraphStore()
    order_set = OrderIntentSet(
        run_id="pm-1",
        approved=(
            OrderIntent(
                ticker="AAPL",
                action="buy",
                quantity=1,
                est_price=Money(amount=Decimal("100.00")),
                rationale=Explanation(summary="pm approved"),
            ),
        ),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-1", source_agent="portfolio_manager"),
    )
    pm = graph.merge_node(
        "PMRun", "pm-1", {"order_intent_set": order_set.model_dump(mode="json")}
    )
    bus = InProcessBus()
    for role in ("proponent", "opponent"):
        DeliberatorAgent(
            bus,
            graph=graph,
            llm=RecordingLLM(peer_answer),
            settings=DeliberatorSettings(role=role, max_rounds=2),
        ).bind()
    settings = DeliberatorSettings(role="manager", max_rounds=2)
    client = _Recording(bus, sender=settings.identity)
    client.requests = []
    manager = DeliberatorAgent(
        bus, graph=graph, llm=RecordingLLM("", judge_answer=_UPHOLD), settings=settings
    )
    review_pm_node(
        pm, graph=graph, manager=manager, peer_client=client, settings=settings
    )
    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    return run, client.requests


def test_the_record_keeps_every_reading_and_the_packet_it_read() -> None:
    """DLIB-OUT-06 / DLIB-OUT-07: each turn's reasoning, each order's packet."""
    run, requests = _review(VALID)

    expected = GuidedReasoning.model_validate(REASONING)
    rows = run.props["transcript"]
    assert [(row["role"], row["round"]) for row in rows] == [
        ("defender", 1),
        ("challenger", 1),
        ("defender", 2),
        ("challenger", 2),
    ]
    for row in rows:
        # The graph freezes nested values; the stored reading rebuilds exactly.
        assert GuidedReasoning.model_validate(row["reasoning"]) == expected
        assert row["reasoning_error"] is None
        assert row["text"] == EXPECTED_TEXT
    sent = {request.proposition for request in requests}
    assert len(sent) == 1
    (proposition,) = sent
    debate = run.props["debates"]["AAPL"]
    assert debate["decision"] == proposition.decision == "buy AAPL (qty 1)"
    assert debate["context"] == proposition.context
    assert debate["context"]


@pytest.mark.parametrize("name", sorted(UNREADABLE))
def test_an_unreadable_reasoning_never_fails_the_turn_or_the_order(name: str) -> None:
    """DLIB-OUT-06 / DLIB-NEV-06: the raw turn is kept and the reason named.

    No fail-open: an unreadable reasoning is a recording gap, not a failed debate,
    so the order is still debated, judged and recorded like any other.
    """
    run, _ = _review(UNREADABLE[name])

    assert run.props["failed_open_count"] == 0
    assert run.props["real_debate_count"] == 1
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    rows = run.props["transcript"]
    assert len(rows) == 4
    for row in rows:
        assert row["reasoning"] is None
        assert row["reasoning_error"]
        assert row["text"] == UNREADABLE[name].strip()
