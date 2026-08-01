"""Deliberator graph-pull manager work.

Agent: deliberator
Role: process pending PMRun nodes by coordinating peer debate and manager verdict.
External I/O: GraphStore and peer-client calls through injected ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.deliberator.context import build_veto_context
from agents.deliberator.store import find_pending as find_pending
from agents.deliberator.store import write_deliberation_run
from contracts.deliberator import (
    DebateProposition,
    DebateRole,
    DebateTurnRecord,
    DebateTurnRequest,
    VerdictRequest,
)
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.deliberator.agent import DeliberatorAgent
    from agents.deliberator.peer_client import PeerClient
    from agents.deliberator.settings import DeliberatorSettings
    from kernel import FaultSink, GraphStore, Node


@dataclass(frozen=True)
class OrderReview:
    """One order's recorded debate outcome."""

    verdict: str
    rationale: str
    turns: tuple[DebateTurnRecord, ...]
    llm_call_keys: tuple[str, ...]


def review_pm_node(
    node: Node,
    *,
    graph: GraphStore,
    manager: DeliberatorAgent,
    peer_client: PeerClient,
    settings: DeliberatorSettings,
    sink: FaultSink | None = None,
) -> None:
    """Review each approved PM order and write one DeliberationRun."""
    sink = sink if sink is not None else CollectingFaultSink()
    order_set = OrderIntentSet.model_validate(node.props["order_intent_set"])
    verdicts: dict[str, str] = {}
    vetoed: list[str] = []
    debates: dict[str, object] = {}
    transcript: list[dict[str, object]] = []
    llm_call_keys: list[str] = []
    for intent in order_set.approved:
        review = _review_one(
            graph, node, order_set, intent, manager, peer_client, settings, sink
        )
        verdicts[intent.ticker] = review.verdict
        debates[intent.ticker] = _debate_record(review)
        transcript.extend(_transcript_records(intent.ticker, review.turns))
        llm_call_keys.extend(review.llm_call_keys)
        if review.verdict != "uphold":
            vetoed.append(intent.ticker)
    write_deliberation_run(
        graph,
        node,
        order_set=order_set,
        verdicts=verdicts,
        vetoed_tickers=vetoed,
        debates=debates,
        narrative=_narrative(debates),
        transcript=transcript,
        role_models=_role_models(settings),
        max_rounds=settings.max_rounds,
        llm_call_keys=llm_call_keys,
    )


def _review_one(
    graph: GraphStore,
    node: Node,
    order_set: OrderIntentSet,
    intent: OrderIntent,
    manager: DeliberatorAgent,
    peer_client: PeerClient,
    settings: DeliberatorSettings,
    sink: FaultSink,
) -> OrderReview:
    """Run all peer turns plus the manager verdict; fail open on faults."""
    result = _fail_open()
    with fault_boundary(
        sink,
        agent="deliberator-manager",
        module="agents.deliberator.poll",
        capability="review_pm_node",
        reraise=False,
    ) as capture:
        proposition = DebateProposition(
            decision=f"{intent.action} {intent.ticker} (qty {intent.quantity})",
            context=build_veto_context(graph, node, order_set, intent),
        )
        result = _debate(
            order_set.run_id, intent.ticker, proposition, manager, peer_client, settings
        )
    return _fail_open() if capture.fault is not None else result


def _debate(
    run_id: str,
    ticker: str,
    proposition: DebateProposition,
    manager: DeliberatorAgent,
    peer_client: PeerClient,
    settings: DeliberatorSettings,
) -> OrderReview:
    transcript: list[DebateTurnRecord] = []
    llm_call_keys: list[str] = []
    for round_number in range(1, settings.max_rounds + 1):
        peers: tuple[tuple[DebateRole, str], ...] = (
            ("defender", settings.proponent_identity),
            ("challenger", settings.opponent_identity),
        )
        for role, recipient in peers:
            request = DebateTurnRequest(
                request_id=f"{run_id}:{ticker}:{role}:r{round_number}",
                proposition=proposition,
                role=role,
                round_number=round_number,
                transcript=tuple(transcript),
            )
            reply = peer_client.debate_turn(recipient, request)
            transcript.append(reply.turn)
            if reply.llm_call_key:
                llm_call_keys.append(reply.llm_call_key)
    verdict = manager.verdict(
        VerdictRequest(
            request_id=f"{run_id}:{ticker}:judge",
            proposition=proposition,
            transcript=tuple(transcript),
        )
    )
    if verdict.llm_call_key:
        llm_call_keys.append(verdict.llm_call_key)
    return OrderReview(
        verdict.ruling,
        verdict.rationale,
        tuple(transcript),
        tuple(llm_call_keys),
    )


def _fail_open() -> OrderReview:
    return OrderReview("uphold", "llm unavailable (fail-open)", (), ())


def _debate_record(review: OrderReview) -> dict[str, object]:
    return {
        "verdict": review.verdict,
        "rationale": review.rationale,
        "turns": [
            {"role": turn.role, "round": turn.round, "text": turn.text}
            for turn in review.turns
        ],
    }


def _transcript_records(
    ticker: str, turns: tuple[DebateTurnRecord, ...]
) -> list[dict[str, object]]:
    return [
        {"ticker": ticker, "role": turn.role, "round": turn.round, "text": turn.text}
        for turn in turns
    ]


def _narrative(debates: dict[str, object]) -> str:
    if not debates:
        return "No PM-approved orders required deliberation."
    return "; ".join(
        f"{ticker}: {record['verdict']} - {record['rationale']}"
        for ticker, record in sorted(debates.items())
        if isinstance(record, dict)
    )


def _role_models(settings: DeliberatorSettings) -> dict[str, str]:
    return {
        "defender": settings.defender_model,
        "challenger": settings.challenger_model,
        "judge": settings.judge_model,
    }
