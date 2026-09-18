"""Judge non-answer fail-open tests.

Agent: deliberator
Role: prove unreadable judge rulings are loud fail-open results.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateTurnRecord, DebateTurnReply, DebateTurnRequest
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import (
    CollectingFaultSink,
    GraphFaultSink,
    InMemoryGraphStore,
    InProcessBus,
    LLMCompletionStoppedError,
    Node,
)


class _SelectiveStoppingPeer:
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
                text=f"{request.role} answered",
            ),
        )


class _JudgeReplyLLM:
    last_stop_reason = "unknown"

    def __init__(self, reply: str) -> None:
        self._reply = reply

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        self.last_stop_reason = "end_turn"
        return self._reply


class _StoppedJudgeLLM:
    last_stop_reason = "unknown"

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        self.last_stop_reason = "max_tokens"
        raise LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens")


def _order(ticker: str, run_id: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary=f"{ticker} approved"),
    )


def _pm_node_for(
    graph: InMemoryGraphStore, run_id: str, tickers: tuple[str, ...]
) -> Node:
    order_set = OrderIntentSet(
        run_id=run_id,
        approved=tuple(_order(ticker, run_id) for ticker in tickers),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id=run_id, source_agent="portfolio_manager"),
    )
    return graph.merge_node(
        "PMRun", run_id, {"order_intent_set": order_set.model_dump(mode="json")}
    )


def _manager_with_llm(graph: InMemoryGraphStore, llm: object) -> DeliberatorAgent:
    return DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=llm,  # type: ignore[arg-type]
        settings=DeliberatorSettings(
            role="manager", instance_name="deliberator-manager"
        ),
    )


@pytest.mark.parametrize(
    ("llm", "reason"),
    [
        (_JudgeReplyLLM("{{{"), "unparseable"),
        (_JudgeReplyLLM(""), "empty"),
        (_StoppedJudgeLLM(), "max_tokens"),
    ],
)
def test_judge_non_answer_fails_open_instead_of_revise(
    llm: object, reason: str
) -> None:
    """DLIB-FAIL-01 / DLIB-FAIL-04 / DLIB-NEV-06: non-answers fail open."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())

    review_pm_node(
        _pm_node_for(graph, "pm-judge", ("AAPL",)),
        graph=graph,
        manager=_manager_with_llm(graph, llm),
        peer_client=_SelectiveStoppingPeer(),
        settings=DeliberatorSettings(role="manager", max_rounds=1),
        sink=sink,
    )

    (run,) = graph.list_nodes("DeliberationRun")
    assert run.props["verdicts"] == {"AAPL": "uphold"}
    assert run.props["vetoed_tickers"] == ()
    assert run.props["failed_open_tickers"] == ("AAPL",)
    assert reason in str(run.props["failed_open_reason"])
    assert run.props["debates"]["AAPL"]["failed_open"] is True
    assert run.props["debates"]["AAPL"]["verdict"] == "uphold"
