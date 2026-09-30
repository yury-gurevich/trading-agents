"""Old deliberation records still read everywhere they are read (S246 B6).

Agent: deliberator
Role: prove a `DeliberationRun` written before S246 (no `reasoning`,
      `reasoning_error`, `decision` or `context`) reads through every reader of
      `transcript` and `debates`, and reads the same as one written after it.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from agents.deliberator.review_record import narrative
from agents.execution.deliberation_gate import (
    deliberation_status,
    drop_vetoed,
    failed_open_tickers,
)
from contracts.common import Explanation, Money, Provenance
from contracts.deliberator import DebateTurnRecord
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, Node
from orchestration.packs.trading_deliberation_view import deliberation
from orchestration.trace_deliberation import format_deliberation_trace
from orchestration.verdict_sources import real_verdicts

_TURN = {"ticker": "AAPL", "role": "defender", "round": 1, "text": "Holds."}
_DEBATE = {
    "verdict": "overturn",
    "rationale": "stop inside one ATR",
    "failed_open": False,
    "failed_open_reason": "",
    "turns": [{"role": "defender", "round": 1, "text": "Holds."}],
}
_OLD = {
    "source_pm_run_id": "pm-1",
    "verdicts": {"AAPL": "overturn", "MSFT": "uphold"},
    "vetoed_tickers": ["AAPL"],
    "debates": {"AAPL": _DEBATE, "MSFT": {**_DEBATE, "verdict": "uphold"}},
    "narrative": "AAPL: overturn - stop inside one ATR",
    "transcript": [_TURN],
    "role_models": {"defender": "m", "challenger": "m", "judge": "m"},
    "max_rounds": 1,
    "real_debate_count": 2,
    "failed_open_count": 0,
    "orphaned_reply_count": 0,
    "failed_open_tickers": [],
    "failed_open_reason": "",
    "created_at": "2026-09-28T22:40:00+00:00",
}
_NEW = {
    **_OLD,
    "transcript": [{**_TURN, "reasoning": None, "reasoning_error": "missing field"}],
    "debates": {
        ticker: {**record, "decision": f"buy {ticker} (qty 1)", "context": "pe: 30"}
        for ticker, record in _OLD["debates"].items()
    },
}


def _run(props: dict[str, object]) -> tuple[InMemoryGraphStore, Node, Node]:
    graph = InMemoryGraphStore()
    order_set = OrderIntentSet(
        run_id="pm-1",
        approved=tuple(
            OrderIntent(
                ticker=ticker,
                action="buy",
                quantity=1,
                est_price=Money(amount=Decimal("100.00")),
                rationale=Explanation(summary="approved"),
            )
            for ticker in ("AAPL", "MSFT")
        ),
        rejected=(),
        explanation=Explanation(summary="sized"),
        provenance=Provenance(run_id="pm-1", source_agent="portfolio_manager"),
    )
    pm = graph.merge_node(
        "PMRun", "pm-1", {"order_intent_set": order_set.model_dump(mode="json")}
    )
    run = graph.merge_node("DeliberationRun", "pm-1", props)
    graph.add_edge(pm, run, "DELIBERATED_BY")
    return graph, pm, run


def _readings(props: dict[str, object]) -> tuple[object, ...]:
    graph, pm, run = _run(props)
    order_set = OrderIntentSet.model_validate(pm.props["order_intent_set"])
    view = deliberation(graph, run)
    return (
        narrative(dict(run.props["debates"])),
        real_verdicts(run.props),
        format_deliberation_trace(pm, run, None),
        (view.observed, view.outputs),
        failed_open_tickers(graph, pm),
        deliberation_status(
            graph,
            pm,
            order_set,
            now=datetime(2026, 9, 29, tzinfo=UTC),
            grace_seconds=900,
        ),
        [i.ticker for i in drop_vetoed(graph, pm, order_set).approved],
    )


def test_every_reader_reads_an_old_record_as_it_reads_a_new_one() -> None:
    """DLIB-OBS-01 / DLIB-OUT-07: the new keys are additive; no reader needs them."""
    old = _readings(_OLD)

    assert old == _readings(_NEW)
    assert old[1] == {"AAPL": "overturn", "MSFT": "uphold"}
    assert old[6] == ["MSFT"]


@pytest.mark.parametrize("row", [_TURN, _NEW["transcript"][0]])
def test_a_turn_row_of_either_shape_validates_as_a_turn_record(
    row: dict[str, object],
) -> None:
    """DLIB-TYP-01: an old row reads as a turn with no reasoning recorded."""
    fields = {key: value for key, value in row.items() if key != "ticker"}
    turn = DebateTurnRecord.model_validate(fields)

    assert (turn.role, turn.round, turn.text) == ("defender", 1, "Holds.")
    assert turn.reasoning is None
