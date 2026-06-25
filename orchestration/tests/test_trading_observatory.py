"""Trading observatory pack tests — per-stage extraction + invariants on a real run.

Agent: orchestration
Role: seed a full in-memory cascade and verify the observatory renders the trade
      spine (provider->pm), passes a clean run, and WARNs on a degraded one and an
      unreached chain.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import DataSource, FakeDataSource
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.packs.trading_observatory import inspect
from orchestration.start import place_run_request
from orchestration.tests.helpers import bar, source


def _cascade(
    data_source: DataSource, tickers: tuple[str, ...], run_id: str
) -> InMemoryGraphStore:
    """Run one full in-memory cascade and return the populated graph."""
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


def test_clean_run_holds_all_invariants() -> None:
    graph = _cascade(source(), ("AAPL", "MSFT"), "obs-ok")
    out = inspect(graph, "obs-ok")
    for stage in (
        "[provider]",
        "[scanner]",
        "[analyst]",
        "[pm]",
        "[execution]",
        "[monitor]",
        "[reporter]",
    ):
        assert stage in out
    assert "<- RunRequest" in out
    assert "<- MarketData(provider)" in out
    # The actual per-stage OUTPUT artifacts are on screen, not just counts.
    assert "tickers   AAPL MSFT" in out
    assert "conf=" in out  # an analyst recommendation row
    assert "qty=" in out  # a PM order row
    assert "submitted=" in out  # execution
    assert "checked=" in out  # monitor
    assert "summary" in out  # reporter
    # The fake source provides no sectors, so the observatory flags the PM
    # concentration caps as INACTIVE (DRIFT-013) — an advisory WARN, not a failure.
    assert "sectors   0/" in out
    assert "WARN  sector_coverage" in out
    # ...and it is the ONLY breach: every blocking data invariant holds.
    assert "1 WARN - inspect above" in out


def test_degraded_run_warns_on_empty_analyst_and_pm() -> None:
    # Bars ~24 calendar days back are stale (>7 trading sessions, DL-10) -> the batch
    # degrades -> the analyst rejects every candidate -> scored=0, and the PM then
    # evaluates nothing. Both floor invariants WARN.
    stale = (
        bar("AAPL", 28, 100.0),
        bar("AAPL", 24, 116.0),
        bar("MSFT", 30, 100.0),
        bar("MSFT", 24, 110.0),
    )
    graph = _cascade(FakeDataSource(bars=stale, vix=12.0), ("AAPL", "MSFT"), "obs-deg")
    out = inspect(graph, "obs-deg")
    assert "quality   DEGRADED" in out  # the root cause is on screen
    assert "REJECT" in out  # the analyst's per-ticker rejections
    assert "WARN  scored: 0 < floor 1.0" in out
    assert "WARN  evaluated: 0 < floor 1.0" in out
    assert "WARN - inspect above" in out


def test_partial_run_marks_every_stage_not_reached() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="obs-partial", tickers=("AAPL",))
    out = inspect(graph, "obs-partial")
    assert "[provider]  <- RunRequest   ... NOT REACHED" in out
    assert "[reporter]  <- MonitorRun(monitor)   ... NOT REACHED" in out
    assert "7 WARN - inspect above" in out
