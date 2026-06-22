"""Local end-to-end demonstrator for the graph-pull pipeline.

Agent: tooling
Role: start the system in one process on an in-memory graph (no store, no Docker) —
      pre-flight checks, the dispatcher places ONE RunRequest, then run each agent's
      graph-pull poll once and print how every downstream agent wakes off its
      prerequisite gate (provider→scanner→analyst→PM→execution→monitor→reporter).
External I/O: stdout (prints the cascade report).

Run it:  PYTHONPATH=. python scripts/run_local.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import all_passed, place_run_request, preflight

_TICKERS = ("AAPL", "MSFT")
_CHAIN = (
    "RunRequest",
    "MarketData",
    "ScanRun",
    "AnalystRun",
    "PMRun",
    "ExecutionRun",
    "MonitorRun",
    "Snapshot",
)


def _bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def _source() -> FakeDataSource:
    bars = (
        _bar("AAPL", 4, 100.0),
        _bar("AAPL", 0, 116.0),
        _bar("MSFT", 6, 100.0),
        _bar("MSFT", 0, 110.0),
    )
    return FakeDataSource(bars=bars, vix=12.0)


def main() -> None:
    """Start the system once and print the graph-pull cascade."""
    graph = InMemoryGraphStore()
    source = _source()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )

    print("PRE-FLIGHT")
    checks = preflight(graph, source=source, tickers=_TICKERS)
    for check in checks:
        mark = "OK " if check.ok else "XX "
        print(f"  [{mark}] {check.name:<24} {check.detail}")
    if not all_passed(checks):
        print("\nPre-flight failed — not starting.")
        return

    print("\nDISPATCHER")
    place_run_request(graph, run_id="local-1", tickers=_TICKERS)
    print(f"  placed RunRequest run-request:local-1 ({len(_TICKERS)} tickers)")

    print("\nCASCADE (one graph-pull pass per agent)")
    for result in cascade_once(graph, provider_agent=agent, broker=PaperBroker()):
        woke = "woke" if result.processed else "idle"
        print(f"  {result.name:<18} {woke}: processed {result.processed}")

    print("\nGRAPH (provenance chain)")
    for label in _CHAIN:
        print(f"  {label:<14} {len(graph.list_nodes(label))}")


if __name__ == "__main__":
    main()
