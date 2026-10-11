"""Past-as-of barrier fixtures and the fleet's upstream find/process pairs.

Agent: orchestration
Role: serve later long bars only when requested, and build real run lineage
      on an in-memory graph for S266's barrier-date regression tests.
External I/O: none (fake source, paper broker, in-process bus).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING

from agents.analyst import poll as analyst_poll
from agents.analyst.settings import AnalystSettings
from agents.execution import poll as execution_poll
from agents.execution.paper_broker import PaperBroker
from agents.forecaster.tests.barrier_helpers import barrier_bars
from agents.monitor import position_sync
from agents.provider import ProviderAgent
from agents.provider import poll as provider_poll
from agents.provider.settings import ProviderSettings
from agents.scanner import poll as scanner_poll
from agents.scanner.settings import ScannerSettings
from kernel import InMemoryGraphStore, InProcessBus
from kernel.work_loop import run_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import ReboundingDataSource, entry_bars

if TYPE_CHECKING:
    from contracts.common import Window
    from contracts.provider import OHLCVBar

TODAY = datetime.now(tz=UTC).date()
LAG = timedelta(days=3)
AS_OF = TODAY - LAG


@dataclass
class PastRunSource(ReboundingDataSource):
    """Short bars for the past run, long bars through today for its history."""

    long: tuple[OHLCVBar, ...] = ()

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        if (window.end - window.start).days < 1000:
            return super().fetch_ohlcv(tickers, window)
        return tuple(
            bar
            for bar in self.long
            if bar.ticker in tickers and window.start <= bar.bar_date <= window.end
        )


def past_run() -> tuple[InMemoryGraphStore, ProviderAgent, PastRunSource]:
    """Place a run three days back; its source can serve three later bars.

    The run's bars are dated from ``AS_OF``, not from a second clock read:
    ``entry_bars`` dates its bars at the call, so with a fixed three-day shift a
    suite that straddled 00:00 UTC put their newest bar a day after the as-of."""
    graph = InMemoryGraphStore()
    fixture = entry_bars()
    shift = max(bar.bar_date for bar in fixture) - AS_OF
    entry = tuple(
        bar.model_copy(update={"bar_date": bar.bar_date - shift}) for bar in fixture
    )
    source = PastRunSource(
        entry=entry,
        rebound=entry,
        long=barrier_bars("AAPL", 800, end=TODAY)
        + barrier_bars("MSFT", 800, end=TODAY),
    )
    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(
        graph, run_id="past-barrier", tickers=("AAPL", "MSFT"), as_of=AS_OF
    )
    return graph, provider, source


def analyze_pending(graph: InMemoryGraphStore) -> None:
    """The analyst's own pair, also used after an analyst-stage resume."""
    result = run_once(
        partial(analyst_poll.find_pending, graph),
        partial(
            analyst_poll.analyze_scan_node, graph=graph, settings=AnalystSettings()
        ),
    )
    assert (result.advanced, result.failed) == (1, 0)


def upstream_once(graph: InMemoryGraphStore, provider: ProviderAgent) -> None:
    """Run the deployed stages' upstream pairs, without the local cascade."""
    broker = PaperBroker()
    run_once(
        partial(execution_poll.find_pending_position_sync, graph),
        partial(execution_poll.sync_run_request, graph=graph, broker=broker),
    )
    run_once(
        partial(position_sync.find_pending_position_sync, graph),
        partial(position_sync.sync_positions_snapshot, graph=graph),
    )
    run_once(
        partial(provider_poll.find_pending, graph),
        partial(provider_poll.ingest_run_node, agent=provider),
    )
    run_once(
        partial(scanner_poll.find_pending, graph),
        partial(scanner_poll.scan_market_node, graph=graph, settings=ScannerSettings()),
    )
    analyze_pending(graph)


def history_once(graph: InMemoryGraphStore, provider: ProviderAgent) -> None:
    """Use the provider's deployed current-work finder and dispatcher."""
    result = run_once(
        partial(provider_poll.find_current_work, graph),
        partial(provider_poll.process_work_item, agent=provider),
    )
    assert (result.advanced, result.failed) == (1, 0)
