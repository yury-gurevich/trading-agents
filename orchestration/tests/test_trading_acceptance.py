"""Trading acceptance pack tests — Layer-3 verdict + cross-stage conservation.

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
from orchestration.observatory import StageView, accept
from orchestration.packs.trading_acceptance import (
    _CONSERVATION,
    accept_run,
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
    assert "PASS" in render_acceptance(result)


def test_broken_chain_is_rejected() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="acc-partial", tickers=("AAPL",))
    result = accept_run(graph, "acc-partial")
    assert not result.passed
    out = render_acceptance(result)
    assert "ACCEPTANCE  FAIL" in out
    assert "NOT REACHED" in out


def test_conservation_catches_a_fabricated_count() -> None:
    # The scanner surfaced 5 names but the provider only ingested 2 — impossible.
    stages = (
        StageView("provider", "x", {"returned": 2}, reached=True),
        StageView("scanner", "y", {"survived": 5}, reached=True),
    )
    result = accept(stages, _CONSERVATION)
    assert not result.passed
    assert any("fabricated" in b.detail for b in result.breaches)
