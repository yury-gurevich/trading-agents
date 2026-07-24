"""Batch trace unit tests.

Agent: orchestration
Role: verify walk_chain and print_trace produce correct results for a full
      in-memory cascade run.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import DataSource, FakeDataSource
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.batch_trace import print_trace, walk_chain
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import bar, entry_bars, source

if TYPE_CHECKING:
    from agents.portfolio_manager.settings import PortfolioManagerSettings


def _cascade(
    data_source: DataSource,
    tickers: tuple[str, ...],
    run_id: str,
    *,
    pm_settings: PortfolioManagerSettings | None = None,
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
    list(
        cascade_once(
            graph, provider_agent=agent, broker=PaperBroker(), pm_settings=pm_settings
        )
    )
    return graph


@pytest.fixture(scope="module")
def full_graph() -> InMemoryGraphStore:
    """Shared graph for all trace tests — built once per module."""
    return _cascade(source(), ("AAPL", "MSFT"), "trace-test")


def test_walk_chain_returns_all_nodes(full_graph: InMemoryGraphStore) -> None:
    """walk_chain should find all 8 nodes in the complete chain."""
    nodes = walk_chain(full_graph, "trace-test")
    assert set(nodes.keys()) == {
        "RunRequest",
        "MarketData",
        "ScanRun",
        "AnalystRun",
        "PMRun",
        "ExecutionRun",
        "MonitorRun",
        "Snapshot",
    }


def test_walk_chain_missing_run_id(full_graph: InMemoryGraphStore) -> None:
    """walk_chain returns empty dict when the run_id is not in the graph."""
    assert walk_chain(full_graph, "does-not-exist") == {}


def test_print_trace_complete(
    full_graph: InMemoryGraphStore, capsys: pytest.CaptureFixture[str]
) -> None:
    """print_trace returns 7 for a complete cascade and outputs all 7 sections."""
    complete = print_trace(full_graph, "trace-test")
    assert complete == 7
    out = capsys.readouterr().out
    for section in (
        "[provider]",
        "[scanner]",
        "[analyst]",
        "[pm]",
        "[execution]",
        "[monitor]",
        "[reporter]",
    ):
        assert section in out
    assert "7/7 stages complete" in out
    assert "OK batch processed" in out
    assert "profit_factor=unavailable" in out
    assert "expectancy_cents=unavailable" in out


def test_print_trace_missing_run_id(
    full_graph: InMemoryGraphStore, capsys: pytest.CaptureFixture[str]
) -> None:
    """print_trace returns 0 for an unknown run_id."""
    complete = print_trace(full_graph, "missing-run")
    assert complete == 0
    assert "not found" in capsys.readouterr().out


def test_print_trace_partial_chain(capsys: pytest.CaptureFixture[str]) -> None:
    """print_trace handles a graph where the chain stops after RunRequest.

    walk_chain finds RunRequest but no downstream nodes — covers the walk_chain
    break branch and all the if-node: False branches inside print_trace.
    """
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="partial", tickers=("AAPL",))
    complete = print_trace(graph, "partial")
    assert complete == 0
    out = capsys.readouterr().out
    assert "[provider]" not in out
    assert "INCOMPLETE" in out


def test_print_trace_with_news_and_drops(capsys: pytest.CaptureFixture[str]) -> None:
    """print_trace covers news headlines and scanner drops.

    NVDA has a -15% return -> scanner drops it (min_relative_strength).
    FakeDataSource has news for AAPL.
    """
    bars = (
        bar("AAPL", 4, 100.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 6, 100.0),
        bar("MSFT", 0, 110.0),
        bar("NVDA", 4, 200.0),
        bar("NVDA", 0, 170.0),  # -15% return -> dropped by min_relative_strength
    )
    src = FakeDataSource(bars=bars, vix=12.0, news={"AAPL": ("breaking: AAPL up",)})
    graph = _cascade(src, ("AAPL", "MSFT", "NVDA"), "drops")
    assert print_trace(graph, "drops") == 7
    out = capsys.readouterr().out
    assert "news" in out
    assert "min_relative_strength" in out


def test_print_trace_degraded_data_exposes_reasons(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """print_trace surfaces the quality block and per-ticker analyst reject reasons.

    Bars older than max_staleness_days (in trading sessions, DL-10) mark the batch
    stale -> provider quality DEGRADED -> analyst rejects every candidate with
    'provider market data degraded'. Covers the quality/stale/notes lines and the
    rejection loop. ~24 calendar days back is well past 7 sessions even with the
    holiday/weekend exclusion.
    """
    bars = (
        bar("AAPL", 28, 100.0),
        bar("AAPL", 24, 116.0),
        bar("MSFT", 30, 100.0),
        bar("MSFT", 24, 110.0),
    )
    graph = _cascade(FakeDataSource(bars=bars, vix=12.0), ("AAPL", "MSFT"), "deg")
    assert print_trace(graph, "deg") == 7
    out = capsys.readouterr().out
    assert "quality   DEGRADED" in out
    assert "stale" in out
    assert "stale_or_missing_tickers" in out
    assert "REJECT  provider market data degraded" in out


def test_print_trace_with_pm_rejection(capsys: pytest.CaptureFixture[str]) -> None:
    """print_trace covers the PM rejected orders branch.

    max_positions=1 forces PM to approve AAPL and reject MSFT (max_positions).
    """
    from agents.portfolio_manager.settings import PortfolioManagerSettings

    graph = _cascade(
        FakeDataSource(bars=entry_bars(), vix=12.0),
        ("AAPL", "MSFT"),
        "pmrej",
        pm_settings=PortfolioManagerSettings(max_positions=1),
    )
    assert print_trace(graph, "pmrej") == 7
    assert "SKIP" in capsys.readouterr().out
