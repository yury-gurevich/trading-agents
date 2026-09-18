"""Trace deliberation defensive-edge tests.

Agent: orchestration
Role: cover malformed historical deliberation trace facts.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import Node
from orchestration.trace_deliberation import format_deliberation_trace


def test_trace_omits_withheld_when_submitted_is_not_numeric() -> None:
    """DLIB-OUT-02 / EXEC-OUT-09: malformed submitted count makes no cause claim."""
    lines = format_deliberation_trace(
        _pm_node(("USB",)),
        _delib_node(("USB",)),
        _exec_node("?"),
    )

    assert not _withheld(lines)


def test_trace_omits_withheld_without_execution_status() -> None:
    """DLIB-OUT-02 / EXEC-OUT-09: absent ExecutionRun renders unknown status."""
    lines = format_deliberation_trace(_pm_node(("USB",)), _delib_node(("USB",)), None)

    assert lines[0] == "reviewed=1  revised=0  vetoed=1  status=?"
    assert not _withheld(lines)


def test_trace_omits_withheld_without_pm_node() -> None:
    """DLIB-OUT-02 / LAW-02: absent PMRun cannot justify a veto cause."""
    lines = format_deliberation_trace(None, _delib_node(("USB",)), _exec_node(0))

    assert not _withheld(lines)


def test_trace_omits_withheld_without_pm_payload() -> None:
    """DLIB-OUT-02 / LAW-02: missing PM payload cannot justify a veto cause."""
    lines = format_deliberation_trace(
        Node("PMRun", "pm", {}),
        _delib_node(("USB",)),
        _exec_node(0),
    )

    assert not _withheld(lines)


def test_trace_omits_withheld_for_invalid_pm_payload() -> None:
    """DLIB-OUT-02 / LAW-02: invalid PM payload cannot justify a veto cause."""
    lines = format_deliberation_trace(
        Node("PMRun", "pm", {"order_intent_set": {"approved": "bad"}}),
        _delib_node(("USB",)),
        _exec_node(0),
    )

    assert not _withheld(lines)


def test_trace_omits_withheld_when_veto_count_does_not_match_gap() -> None:
    """DLIB-OUT-02 / LAW-02: veto count must exactly match submitted gap."""
    lines = format_deliberation_trace(
        _pm_node(("USB", "WFC")),
        _delib_node(("USB",)),
        _exec_node(0),
    )

    assert not _withheld(lines)


def test_trace_omits_withheld_for_unapproved_veto_ticker() -> None:
    """DLIB-OUT-02 / LAW-02: vetoed tickers must be approved buy tickers."""
    lines = format_deliberation_trace(
        _pm_node(("USB", "WFC")),
        _delib_node(("AMZN",)),
        _exec_node(1),
    )

    assert not _withheld(lines)


def _pm_node(tickers: tuple[str, ...]) -> Node:
    return Node(
        "PMRun",
        "pm",
        {"order_intent_set": _order_set(tickers).model_dump(mode="json")},
    )


def _delib_node(vetoed: tuple[str, ...]) -> Node:
    return Node(
        "DeliberationRun",
        "delib",
        {"verdicts": dict.fromkeys(vetoed, "overturn"), "vetoed_tickers": vetoed},
    )


def _exec_node(submitted: object) -> Node:
    return Node(
        "ExecutionRun",
        "exec",
        {"submitted": submitted, "deliberation_status": "applied"},
    )


def _order_set(tickers: tuple[str, ...]) -> OrderIntentSet:
    return OrderIntentSet(
        run_id="pm",
        approved=tuple(_intent(ticker) for ticker in tickers),
        rejected=(),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id="pm", source_agent="portfolio_manager"),
    )


def _intent(ticker: str) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=1,
        est_price=Money(amount=Decimal("100.00")),
        rationale=Explanation(summary="fixture"),
    )


def _withheld(lines: tuple[str, ...]) -> bool:
    return any(line.startswith("withheld=") for line in lines)
