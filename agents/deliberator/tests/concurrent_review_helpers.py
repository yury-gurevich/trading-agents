"""Helpers for deliberator concurrent order-review tests.

Agent: deliberator
Role: provide deterministic delayed peers and PMRun fixtures for S172 tests.
External I/O: none.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from typing import Literal

from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATION_RUN_LABEL, PRODUCED_BY_EDGE
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import (
    DebateTurnRecord,
    DebateTurnReply,
    DebateTurnRequest,
    VerdictReply,
    VerdictRequest,
)
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, Node

TICKERS = ("AAPL", "MSFT", "GOOG", "AMZN")
_OVERTURNED = frozenset({"MSFT", "AMZN"})


class DelayedPeer:
    def __init__(
        self, graph: InMemoryGraphStore, *, fail_ticker: str | None = None
    ) -> None:
        self._graph = graph
        self._fail_ticker = fail_ticker
        self._lock = threading.Lock()
        self._active = 0
        self.max_active = 0

    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        ticker = _ticker_from_request(request.request_id)
        if ticker == self._fail_ticker:
            raise RuntimeError(f"planted failure for {ticker}")
        self._enter_call()
        try:
            time.sleep(_delay(ticker))
        finally:
            self._leave_call()
        key = f"{request.request_id}:llm"
        self._graph.merge_node("LLMCall", key, {"calling_agent": recipient})
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text=f"{ticker} {request.role}",
            ),
            llm_call_key=key,
        )

    def _enter_call(self) -> None:
        with self._lock:
            self._active += 1
            self.max_active = max(self.max_active, self._active)

    def _leave_call(self) -> None:
        with self._lock:
            self._active -= 1


class Manager:
    def __init__(self, graph: InMemoryGraphStore) -> None:
        self._graph = graph

    def verdict(self, request: VerdictRequest) -> VerdictReply:
        ticker = _ticker_from_request(request.request_id)
        ruling: Literal["uphold", "overturn", "revise"]
        ruling = "overturn" if ticker in _OVERTURNED else "uphold"
        key = f"{request.request_id}:llm"
        self._graph.merge_node("LLMCall", key, {"calling_agent": "manager"})
        return VerdictReply(
            request_id=request.request_id,
            ruling=ruling,
            rationale=f"{ticker} reviewed",
            llm_call_key=key,
        )


def run_review(
    concurrency: int,
    *,
    tickers: tuple[str, ...] = TICKERS,
    fail_ticker: str | None = None,
) -> tuple[Node, DelayedPeer, InMemoryGraphStore]:
    graph = InMemoryGraphStore()
    pm = _pm_node(graph, tickers)
    peer = DelayedPeer(graph, fail_ticker=fail_ticker)
    settings = DeliberatorSettings(
        role="manager",
        instance_name="deliberator-manager",
        max_rounds=1,
        debate_concurrency=concurrency,
    )
    review_pm_node(
        pm,
        graph=graph,
        manager=Manager(graph),  # type: ignore[arg-type]
        peer_client=peer,
        settings=settings,
    )
    (run,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
    return run, peer, graph


def ordered_props(run: Node, graph: InMemoryGraphStore) -> tuple[object, ...]:
    return (
        tuple(run.props["verdicts"].items()),
        run.props["vetoed_tickers"],
        tuple(run.props["debates"].items()),
        run.props["transcript"],
        tuple(
            node.key
            for node in graph.descendants(
                run, max_depth=1, edge_types={PRODUCED_BY_EDGE}
            )
        ),
    )


def _pm_node(graph: InMemoryGraphStore, tickers: tuple[str, ...]) -> Node:
    order_set = OrderIntentSet(
        run_id="pm-concurrency",
        approved=tuple(_intent(ticker) for ticker in tickers),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(
            run_id="pm-concurrency", source_agent="portfolio_manager"
        ),
    )
    return graph.merge_node(
        "PMRun",
        order_set.run_id,
        {"order_intent_set": order_set.model_dump(mode="json")},
    )


def _intent(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary=f"{ticker} approved"),
    )


def _ticker_from_request(request_id: str) -> str:
    return request_id.split(":")[1]


def _delay(ticker: str) -> float:
    return 0.005 * (len(TICKERS) - TICKERS.index(ticker))
