"""Acceptance outcome tests — a run must prove it traded, not that it tried.

Agent: orchestration
Role: the DL-59 truth table — every order rejected is FAIL, orders still queued are
      UNPROVEN, one fill is enough to PASS, and a no-trade day stays NO_TRADE.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.observatory import StageView
from orchestration.packs.trading_acceptance import (
    accept_run,
    evaluate_stages,
    render_acceptance,
)
from orchestration.start import place_run_request
from orchestration.tests.helpers import source
from orchestration.tests.test_trading_acceptance import _complete_stages


def test_run_whose_every_order_was_rejected_fails() -> None:
    """DL-59: submitting is not trading. The 07-21 signature — five orders placed,
    all rejected at the open for want of buying power — must not read PASS."""
    stages = _complete_stages(scored=5, filled=0, unfilled=5, statuses="rejected")

    result = evaluate_stages(stages, rejection_evidence=False)

    assert result.verdict == "FAIL"
    assert not result.passed
    detail = next(b.detail for b in result.breaches if b.key == "filled")
    assert "0 of 5 submitted orders filled" in detail
    assert "rejected" in detail
    assert "traded nothing" in detail


def test_unresolved_orders_are_unproven_not_passed() -> None:
    """DL-59: the 07-22 signature — orders queued after the close. Not a fault, but
    success is not proven either, so it must never render as PASS (LAW-02)."""
    stages = _complete_stages(scored=5, filled=0, unfilled=0, statuses="pending")

    result = evaluate_stages(stages, rejection_evidence=False)

    assert result.verdict == "UNPROVEN"
    assert result.passed  # queued orders do not block a deploy
    out = render_acceptance(result)
    assert "ACCEPTANCE  UNPROVEN" in out
    assert "PASS" not in out


def test_one_fill_is_enough_to_prove_the_run_traded() -> None:
    """A partly rejected batch still traded; only a wholly unfilled batch fails."""
    stages = _complete_stages(
        scored=5, filled=1, unfilled=4, statuses="filled, rejected"
    )

    result = evaluate_stages(stages, rejection_evidence=False)

    assert result.verdict == "PASS"


def test_no_trade_day_is_not_reclassified_as_unproven() -> None:
    """A run that submitted nothing has nothing to resolve — NO_TRADE must survive."""
    stages = _complete_stages(scored=0, filled=0, unfilled=0, statuses="")

    result = evaluate_stages(stages, rejection_evidence=True)

    assert result.verdict == "NO_TRADE"


def test_broker_refusing_every_order_fails_end_to_end() -> None:
    """DL-59: a full cascade whose broker refuses every order reads FAIL, not PASS.

    Scored from the Fill nodes rather than ExecutionRun.submitted: a synchronous
    refusal leaves submitted=0, so an intent-based check would call this a clean run.
    """
    graph = InMemoryGraphStore()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id="acc-refused", tickers=("AAPL", "MSFT"))
    list(
        cascade_once(
            graph,
            provider_agent=agent,
            broker=PaperBroker(reject_tickers={"AAPL", "MSFT"}),
        )
    )

    result = accept_run(graph, "acc-refused")

    assert result.verdict == "FAIL"
    assert not result.passed
    assert any("traded nothing" in b.detail for b in result.breaches)


def test_unproven_needs_a_reached_execution_stage_with_counts() -> None:
    """The outcome verdict is evidence-driven: no execution stage, or a stage whose
    counts are missing, must not be guessed into UNPROVEN."""
    complete = _complete_stages(scored=1)
    without_execution = tuple(s for s in complete if s.name != "execution")
    missing = evaluate_stages(without_execution, rejection_evidence=False)
    assert missing.verdict == "PASS"

    unreached = tuple(
        StageView(s.name, s.trigger, s.observed, reached=False, checks=s.checks)
        if s.name == "execution"
        else s
        for s in complete
    )
    assert evaluate_stages(unreached, rejection_evidence=False).verdict == "FAIL"

    uncounted = tuple(
        StageView(s.name, s.trigger, {"submitted": 1}, reached=True)
        if s.name == "execution"
        else s
        for s in complete
    )
    assert evaluate_stages(uncounted, rejection_evidence=False).verdict == "PASS"
