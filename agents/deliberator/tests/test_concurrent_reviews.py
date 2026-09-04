"""Deliberator concurrent order-review tests.

Agent: deliberator
Role: prove independent PM-approved orders can fan out without changing records.
External I/O: none.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.concurrent_review_helpers import (
    TICKERS,
    ordered_props,
    run_review,
)
from kernel.config import describe


def test_debate_concurrency_is_bounded_tunable() -> None:
    """DLIB-DEP-04 / DRIFT-041: order fan-out is bounded configuration."""
    docs = {item.name: item for item in describe(DeliberatorSettings)}

    item = docs["debate_concurrency"]

    assert item.env_var == "DELIBERATOR_DEBATE_CONCURRENCY"
    assert item.default == 4
    assert item.minimum == 1.0
    assert item.maximum == 25.0
    assert "vendor rate limit" in item.justification
    assert DeliberatorSettings(debate_concurrency=1).debate_concurrency == 1
    with pytest.raises(ValidationError):
        DeliberatorSettings(debate_concurrency=0)


def test_concurrent_reviews_preserve_durable_order() -> None:
    """DLIB-ORD-01 / DLIB-OUT-02 / DLIB-OBS-01: K=4 keeps PM order."""
    serial_run, serial_peer, serial_graph = run_review(1)
    concurrent_run, concurrent_peer, concurrent_graph = run_review(4)

    assert serial_peer.max_active == 1
    assert concurrent_peer.max_active > 1
    assert ordered_props(serial_run, serial_graph) == ordered_props(
        concurrent_run, concurrent_graph
    )
    assert list(concurrent_run.props["verdicts"]) == list(TICKERS)
    assert concurrent_run.props["vetoed_tickers"] == ("MSFT", "AMZN")
    assert [row["ticker"] for row in concurrent_run.props["transcript"]] == [
        ticker for ticker in TICKERS for _ in range(2)
    ]
    assert [row["role"] for row in concurrent_run.props["transcript"]] == [
        role for _ in TICKERS for role in ("defender", "challenger")
    ]


def test_single_order_failure_is_isolated_under_concurrency() -> None:
    """DLIB-FAIL-01 / DLIB-OUT-02: one failed order leaves peers intact."""
    run, peer, _graph = run_review(
        3, tickers=("AAPL", "MSFT", "GOOG"), fail_ticker="MSFT"
    )

    assert peer.max_active > 1
    assert list(run.props["verdicts"]) == ["AAPL", "MSFT", "GOOG"]
    assert run.props["verdicts"] == {
        "AAPL": "uphold",
        "MSFT": "uphold",
        "GOOG": "uphold",
    }
    assert run.props["vetoed_tickers"] == ()
    assert run.props["real_debate_count"] == 2
    assert run.props["failed_open_count"] == 1
    assert run.props["failed_open_tickers"] == ("MSFT",)
    assert run.props["failed_open_reason"] == "RuntimeError: planted failure for MSFT"
    assert run.props["debates"]["MSFT"]["failed_open"] is True
    assert run.props["debates"]["AAPL"]["failed_open"] is False
    assert run.props["debates"]["GOOG"]["failed_open"] is False
