"""Deliberator stop-reason fail-open tests.

Agent: deliberator
Role: prove stopped LLM completions stay per-order and keep evidence sanitized.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import (
    DebateProposition,
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
)
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import (
    CollectingFaultSink,
    FakeLLMClient,
    GraphFaultSink,
    InMemoryGraphStore,
    InProcessBus,
    LLMCompletionStoppedError,
    Node,
)

_UPHOLD = '{"ruling": "uphold", "rationale": "clears review"}'
_SENTINEL = "SENTINEL_PROMPT_PAYLOAD"


class _SelectiveStoppingPeer:
    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        del recipient
        if request.request_id == "pm-two:MSFT:defender:r1":
            raise LLMCompletionStoppedError(
                provider="anthropic", stop_reason="max_tokens"
            )
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text=f"{request.role} answered",
            ),
        )


class _NormalStopLLM:
    last_stop_reason = "unknown"

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        self.last_stop_reason = "end_turn"
        return "normal answer"


class _StoppingLLM:
    last_stop_reason = "unknown"

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, tool_schema
        assert _SENTINEL in user
        self.last_stop_reason = "max_tokens"
        raise LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens")


def _order(ticker: str, run_id: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary=f"{ticker} {_SENTINEL} approved"),
    )


def _pm_node(graph: InMemoryGraphStore) -> Node:
    order_set = OrderIntentSet(
        run_id="pm-two",
        approved=(_order("AAPL", "pm-two"), _order("MSFT", "pm-two")),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-two", source_agent="portfolio_manager"),
    )
    return graph.merge_node(
        "PMRun", "pm-two", {"order_intent_set": order_set.model_dump(mode="json")}
    )


def _manager(graph: InMemoryGraphStore) -> DeliberatorAgent:
    return DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=DeliberatorSettings(
            role="manager", instance_name="deliberator-manager"
        ),
    )


def _turn_request(request_id: str, context: str) -> DebateTurnRequest:
    return DebateTurnRequest(
        request_id=request_id,
        proposition=DebateProposition(decision="buy AAPL", context=context),
        role="defender",
        round_number=1,
    )


def test_one_stopped_turn_fails_only_that_order_and_records_reason() -> None:
    """DLIB-FAIL-01 / DLIB-FAIL-04 / DLIB-NEV-06 / DLIB-NEV-07: one stop fails."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())

    review_pm_node(
        _pm_node(graph),
        graph=graph,
        manager=_manager(graph),
        peer_client=_SelectiveStoppingPeer(),
        settings=DeliberatorSettings(role="manager", max_rounds=1),
        sink=sink,
    )

    (run,) = graph.list_nodes("DeliberationRun")
    assert run.props["verdicts"] == {"AAPL": "uphold", "MSFT": "uphold"}
    assert run.props["real_debate_count"] == 1
    assert run.props["failed_open_count"] == 1
    assert run.props["failed_open_tickers"] == ("MSFT",)
    assert "max_tokens" in str(run.props["failed_open_reason"])
    assert all(record["ticker"] == "AAPL" for record in run.props["transcript"])
    assert all(record["text"] for record in run.props["transcript"])
    evidence = repr(run.props)
    assert _SENTINEL not in evidence
    (fault,) = graph.list_nodes("Fault")
    assert _SENTINEL not in repr(fault.props)


def test_llmcall_records_stop_reason_without_payload() -> None:
    """DLIB-OUT-03 / DLIB-OUT-05: LLMCall stop reasons are payload-free."""
    graph = InMemoryGraphStore()
    normal = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=_NormalStopLLM(),
        settings=DeliberatorSettings(role="proponent"),
    )
    stopped = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=_StoppingLLM(),
        settings=DeliberatorSettings(role="proponent"),
    )

    reply = normal.debate_turn(_turn_request("normal-1", "ordinary context"))
    assert reply.llm_call_key is not None
    normal_call = graph.get_node("LLMCall", reply.llm_call_key)
    assert normal_call is not None
    assert normal_call.props["stop_reason"] == "end_turn"

    with pytest.raises(LLMCompletionStoppedError, match="max_tokens") as exc:
        stopped.debate_turn(_turn_request("stopped-1", _SENTINEL))

    assert _SENTINEL not in str(exc.value)
    stopped_call = graph.get_node("LLMCall", "llmcall:deliberator-proponent:stopped-1")
    assert stopped_call is not None
    assert stopped_call.props["stop_reason"] == "max_tokens"
    node_evidence = repr(stopped_call.props)
    assert _SENTINEL not in node_evidence
    assert "normal answer" not in repr(normal_call.props)
