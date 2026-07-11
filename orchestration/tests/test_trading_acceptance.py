"""Trading acceptance pack tests — verdict truth table + conservation.

Agent: orchestration
Role: a clean cascade PASSES, a broken chain FAILS, and a fabricated count (a stage
      that output more than its input) is caught by the conservation boundary.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.observatory import Breach, Check, StageView, accept
from orchestration.packs.trading_acceptance import (
    _CONSERVATION,
    _explains_floor,
    _is_no_trade,
    accept_run,
    evaluate_stages,
    render_acceptance,
)
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    from agents.provider.sources import DataSource


def _cascade(
    data_source: DataSource, tickers: tuple[str, ...], run_id: str
) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=data_source,
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id=run_id, tickers=tickers)
    list(cascade_once(graph, provider_agent=agent, broker=PaperBroker()))
    return graph


def test_clean_cascade_is_accepted() -> None:
    graph = _cascade(source(), ("AAPL", "MSFT"), "acc-ok")
    result = accept_run(graph, "acc-ok")
    assert result.passed
    assert result.verdict == "PASS"
    assert "PASS" in render_acceptance(result)


def test_broken_chain_is_rejected() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="acc-partial", tickers=("AAPL",))
    result = accept_run(graph, "acc-partial")
    assert not result.passed
    out = render_acceptance(result)
    assert "ACCEPTANCE  FAIL" in out
    assert "NOT REACHED" in out


def _complete_stages(scored: int) -> tuple[StageView, ...]:
    """Minimal complete pipeline for the pack-level truth table."""
    return (
        StageView("provider", "x", {"returned": 1}, reached=True),
        StageView("scanner", "x", {"survived": 1}, reached=True),
        StageView(
            "analyst",
            "x",
            {"scored": scored},
            reached=True,
            checks=(Check("scored", "floor", 1.0),),
        ),
        StageView(
            "pm",
            "x",
            {"approved": scored, "evaluated": scored},
            reached=True,
            checks=(Check("evaluated", "floor", 1.0),),
        ),
        StageView("execution", "x", {"submitted": scored}, reached=True),
        StageView("monitor", "x", {"checked": scored}, reached=True),
        StageView("reporter", "x", {"summary": "done"}, reached=True),
    )


def test_complete_scored_truth_table_passes() -> None:
    result = evaluate_stages(_complete_stages(scored=1), rejection_evidence=False)
    assert result.verdict == "PASS"
    assert result.passed


def test_complete_zero_scored_with_evidence_is_no_trade() -> None:
    result = evaluate_stages(_complete_stages(scored=0), rejection_evidence=True)
    assert result.verdict == "NO_TRADE"
    assert result.passed
    assert "ACCEPTANCE  NO_TRADE" in render_acceptance(result)


def test_zero_scored_without_evidence_fails() -> None:
    result = evaluate_stages(_complete_stages(scored=0), rejection_evidence=False)
    assert result.verdict == "FAIL"
    assert not result.passed


def test_missing_stage_truth_table_fails_even_with_evidence() -> None:
    stages = (
        *_complete_stages(scored=0)[:-1],
        StageView("reporter", "x", {}, reached=False),
    )
    result = evaluate_stages(stages, rejection_evidence=True)
    assert result.verdict == "FAIL"
    assert not result.passed


def test_rejection_evidence_must_include_values_that_missed_the_floor() -> None:
    assert _explains_floor(
        {"ticker": "AAPL", "reason": "confidence 0.527 below regime floor 0.600"}
    )
    assert not _explains_floor(
        {"ticker": "AAPL", "reason": "confidence below regime floor"}
    )
    assert not _explains_floor(
        {"ticker": "AAPL", "reason": "confidence 0.700 below regime floor 0.600"}
    )
    assert not _explains_floor("not a rejection record")


def test_nonzero_scored_run_cannot_be_reclassified_as_no_trade() -> None:
    breaches = (Breach("pm", "evaluated", "0 < floor 1.0"),)
    assert not _is_no_trade(_complete_stages(scored=1), breaches, True)


def test_conservation_catches_a_fabricated_count() -> None:
    # The scanner surfaced 5 names but the provider only ingested 2 — impossible.
    stages = (
        StageView("provider", "x", {"returned": 2}, reached=True),
        StageView("scanner", "y", {"survived": 5}, reached=True),
    )
    result = accept(stages, _CONSERVATION)
    assert not result.passed
    assert any("fabricated" in b.detail for b in result.breaches)
