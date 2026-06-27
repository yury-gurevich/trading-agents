"""Deliberation challenger-veto stage — an LLM may block a PM-approved trade.

Agent: orchestration
Role: after the PM approves orders, run a bounded defend/challenge/judge debate
      (kernel.deliberate) on each approved order. A non-uphold verdict VETOES that
      order; the judge may only SUBTRACT, never originate or resize (DL-31 — the LLM
      analogue of FORE-NEV-02). Records a DeliberationRun with the per-order verdicts
      and the vetoed tickers; execution drops the vetoed tickers. Fail-open: an LLM
      outage upholds (never blocks trading on an error) but is recorded as a fault.
External I/O: none directly (the model is reached via the injected LLMClient).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import CollectingFaultSink, Proposition, deliberate
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from kernel import DebateResult, FaultSink, GraphStore, LLMClient, Node

PM_RUN_LABEL = "PMRun"
DELIBERATION_RUN_LABEL = "DeliberationRun"
DELIBERATED_EDGE = "DELIBERATED_BY"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return PMRun nodes with no DeliberationRun yet (unprocessed work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(PM_RUN_LABEL):
        done = list(graph.descendants(node, max_depth=1, edge_types={DELIBERATED_EDGE}))
        if not done:
            pending.append(node)
    return pending


def deliberate_pm_node(
    node: Node,
    *,
    graph: GraphStore,
    llm: LLMClient,
    max_rounds: int = 1,
    sink: FaultSink | None = None,
) -> None:
    """Debate each PM-approved order; record verdicts + the vetoed (subtracted) set."""
    sink = sink if sink is not None else CollectingFaultSink()
    order_set = OrderIntentSet.model_validate(node.props["order_intent_set"])
    verdicts: dict[str, str] = {}
    vetoed: list[str] = []
    debates: dict[str, object] = {}
    for intent in order_set.approved:
        result = _review(llm, intent, order_set.run_id, sink, max_rounds)
        ruling = result.verdict.ruling if result is not None else "uphold"
        verdicts[intent.ticker] = ruling
        debates[intent.ticker] = _record(result)
        if ruling != "uphold":
            vetoed.append(intent.ticker)
    run = graph.merge_node(
        DELIBERATION_RUN_LABEL,
        order_set.run_id,
        {
            "source_pm_run_id": order_set.run_id,
            "verdicts": verdicts,
            "vetoed_tickers": vetoed,
            # The full transcript per order — the auditable "why" behind each ruling.
            "debates": debates,
        },
    )
    graph.add_edge(node, run, DELIBERATED_EDGE)


def _record(result: DebateResult | None) -> dict[str, object]:
    """Serialise one order's debate for the graph; a fail-open fault has no turns."""
    if result is None:
        return {
            "verdict": "uphold",
            "rationale": "llm unavailable (fail-open)",
            "turns": [],
        }
    return {
        "verdict": result.verdict.ruling,
        "rationale": result.verdict.rationale,
        "turns": [
            {"role": t.role, "round": t.round, "text": t.text}
            for t in result.transcript
        ],
    }


def _review(
    llm: LLMClient,
    intent: OrderIntent,
    run_id: str,
    sink: FaultSink,
    max_rounds: int,
) -> DebateResult | None:
    """One order's full debate; fail-open to ``None`` (→ uphold) on any LLM fault."""
    result: DebateResult | None = None
    with fault_boundary(
        sink,
        agent="deliberation",
        module="orchestration.veto",
        capability="deliberate",
        reraise=False,
    ) as capture:
        proposition = Proposition(
            decision=f"{intent.action} {intent.ticker} (qty {intent.quantity})",
            context=f"A PM-approved order from run {run_id}; review before execution.",
        )
        result = deliberate(llm, proposition, max_rounds=max_rounds)
    return None if capture.fault is not None else result
