"""Deliberator graph-pull manager work.

Agent: deliberator
Role: process pending PMRun nodes by coordinating peer debate and manager verdict.
External I/O: GraphStore and peer-client calls through injected ports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.context import build_veto_context
from agents.deliberator.peer_client import orphaned_reply_count_from
from agents.deliberator.review_record import (
    OrderReview,
    debate_record,
    fail_open_review,
    failed_open_reason,
    narrative,
    role_models,
    transcript_records,
)
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
    from kernel import AgentFault, FaultSink, GraphStore, Node


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
    if not _preflight_peers(peer_client, settings, sink):
        return
    order_set = OrderIntentSet.model_validate(node.props["order_intent_set"])
    verdicts: dict[str, str] = {}
    vetoed: list[str] = []
    debates: dict[str, object] = {}
    transcript: list[dict[str, object]] = []
    llm_call_keys: list[str] = []
    real_debate_count = 0
    orphaned_reply_count_before = orphaned_reply_count_from(peer_client)
    failed_open_tickers: list[str] = []
    failed_open_reasons: list[str] = []
    for intent in order_set.approved:
        review = _review_one(
            graph, node, order_set, intent, manager, peer_client, settings, sink
        )
        verdicts[intent.ticker] = review.verdict
        debates[intent.ticker] = debate_record(review)
        transcript.extend(transcript_records(intent.ticker, review.turns))
        llm_call_keys.extend(review.llm_call_keys)
        if review.turns:
            real_debate_count += 1
        if review.failed_open:
            failed_open_tickers.append(intent.ticker)
            failed_open_reasons.append(review.failed_open_reason)
        if review.verdict != "uphold":
            vetoed.append(intent.ticker)
    write_deliberation_run(
        graph,
        node,
        order_set=order_set,
        verdicts=verdicts,
        vetoed_tickers=vetoed,
        debates=debates,
        narrative=narrative(debates),
        transcript=transcript,
        role_models=role_models(settings),
        max_rounds=settings.max_rounds,
        real_debate_count=real_debate_count,
        failed_open_count=len(failed_open_tickers),
        orphaned_reply_count=orphaned_reply_count_from(peer_client)
        - orphaned_reply_count_before,
        failed_open_tickers=failed_open_tickers,
        failed_open_reason=_combined_failed_open_reason(failed_open_reasons),
        llm_call_keys=llm_call_keys,
    )


def _preflight_peers(
    peer_client: PeerClient, settings: DeliberatorSettings, sink: FaultSink
) -> bool:
    """Return false when configured peers cannot be addressed."""
    with fault_boundary(
        sink,
        agent="deliberator-manager",
        module="agents.deliberator.poll",
        capability="peer_preflight",
        reraise=False,
    ) as capture:
        peer_client.preflight((settings.proponent_identity, settings.opponent_identity))
    return capture.fault is None


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
    result = fail_open_review()
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
    if capture.fault is not None:
        return fail_open_review(_reason_from_fault(capture.fault))
    return result


def _reason_from_fault(fault: AgentFault) -> str:
    return failed_open_reason(fault.error_type, fault.message)


def _combined_failed_open_reason(reasons: list[str]) -> str:
    return "; ".join(dict.fromkeys(reasons))


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
