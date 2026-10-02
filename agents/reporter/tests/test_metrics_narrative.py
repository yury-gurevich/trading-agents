"""Reporter domain unit tests.

Agent: reporter
Role: verify metric reducers and narrative composition edge cases.
External I/O: none.
"""

from __future__ import annotations

from agents.reporter.domain.metrics import (
    collect_portfolio_metrics,
    collect_regime_attribution,
    collect_signal_metrics,
)
from agents.reporter.domain.narrative import UNAVAILABLE, compose_story
from kernel import Node


def test_metrics_collect_counts_averages_and_regime_context() -> None:
    pm_run = Node("PMRun", "pm", {"approved_count": 2, "rejected_count": 1})
    closes = (
        Node("CloseDecision", "stop", {"trigger": "stop"}),
        Node("CloseDecision", "target", {"trigger": "target"}),
        Node("CloseDecision", "time", {"trigger": "time"}),
    )
    recommendations = (
        Node("Recommendation", "a", {"confidence": 0.8, "technical_score": 0.7}),
        Node("Recommendation", "b", {"confidence": 0.6, "technical_score": 0.5}),
    )
    portfolio = collect_portfolio_metrics(pm_run, closes)
    signal = collect_signal_metrics(recommendations, rejection_count=3)
    regime = collect_regime_attribution(
        (Node("ScanRun", "scan"),),
        (Node("MarketSnapshot", "market", {"bar_count": 5}),),
    )
    # The book counts and the stop trigger come from the broker's fills (S253).
    assert "positions_closed" not in portfolio
    assert "close_trigger_stop" not in portfolio
    assert portfolio["close_trigger_target"] == 1.0
    assert portfolio["close_trigger_time"] == 1.0
    assert portfolio["approval_rate"] == 2 / 3
    assert signal["avg_confidence"] == 0.7
    assert signal["rejection_count"] == 3.0
    assert regime == {"snapshots_used": 1.0, "bar_count_total": 5.0}


def test_metrics_handle_empty_and_bad_numeric_values() -> None:
    signal = collect_signal_metrics(
        (Node("Recommendation", "bad", {"confidence": "bad"}),)
    )
    assert collect_portfolio_metrics(None, ())["approval_rate"] == 0.0
    assert signal["avg_confidence"] == 0.0
    assert collect_regime_attribution((), ()) == {}


def test_the_pm_decision_counts_are_reported_as_decided() -> None:
    """RPT-IDN-01 / RPT-NEV-01 / RPT-TYP-02: the PM's counts are projected, as floats.

    A dropped order is not a rejection; the reporter re-decides nothing. The three
    keys that described the run's own orders are gone (S253).
    """
    pm_run = Node("PMRun", "pm", {"approved_count": 3, "rejected_count": 1})

    portfolio = collect_portfolio_metrics(pm_run, ())

    assert portfolio["approved_count"] == 3.0
    assert portfolio["rejected_count"] == 1.0
    assert all(isinstance(value, float) for value in portfolio.values())
    for removed in (
        "execution_count",
        "dropped_decision_count",
        "approval_execution_gap",
    ):
        assert removed not in portfolio


def test_compose_story_uses_full_lineage_and_close_decision() -> None:
    story = compose_story(
        Node("Position", "pm:AAPL", {"ticker": "AAPL", "opened_price_cents": 10100}),
        Node("Fill", "fill", {"ticker": "AAPL"}),
        Node(
            "OrderIntent",
            "order",
            {
                "ticker": "AAPL",
                "action": "buy",
                "quantity": 3,
                "est_price_cents": 10100,
                "stop_pct": 0.05,
                "target_pct": 0.1,
            },
        ),
        Node("Recommendation", "rec", {"confidence": 0.82, "technical_score": 0.77}),
        Node("Candidate", "candidate", {"rank": 1, "score": 0.91}),
        Node("ScanRun", "scan", {"created_at": "2026-06-10"}),
        Node("CloseDecision", "close", {"trigger": "stop", "rationale": "Hit stop."}),
    )
    assert "AAPL scanned [2026-06-10]" in story
    assert "confidence 82% -> buy" in story
    assert "Exit: stop - Hit stop." in story


def test_compose_story_marks_missing_and_bad_data_without_crashing() -> None:
    bad = Node(
        "OrderIntent",
        "bad",
        {
            "action": "buy",
            "quantity": 1,
            "est_price_cents": "bad",
            "stop_pct": "bad",
        },
    )
    story = compose_story(
        None,
        None,
        bad,
        Node("Recommendation", "bad", {"technical_score": "bad"}),
        Node("Candidate", "bad", {"score": "bad"}),
        None,
        None,
    )
    assert UNAVAILABLE in story
    assert "Position still open." in story
    missing = compose_story(None, None, None, None, None, None, None)
    assert UNAVAILABLE in missing
