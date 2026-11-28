"""Local end-to-end demonstrator for the graph-pull pipeline.

Agent: tooling
Role: start the system in one process — pre-flight checks, the dispatcher places ONE
      RunRequest, then run each agent's graph-pull poll once and print how every
      downstream agent wakes off its prerequisite gate
      (provider → scanner → analyst → PM → execution → monitor → reporter).
      In-memory graph + FakeDataSource only; no flag reaches further (DL-329).
      A run on real data is the test lane's: `scripts/run_lane.py` (DL-328).
External I/O: stdout. No network, no database, no model call; the agents' settings
      read a `.env` in the working directory, as every agent's do.

Run it:
  PYTHONPATH=. python scripts/run_local.py                     # the cascade
  PYTHONPATH=. python scripts/run_local.py --trace --observe   # + trace, observatory
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import all_passed, place_run_request, preflight

_TICKERS_DEMO: tuple[str, ...] = ("AAPL", "MSFT")
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


def _fake_source() -> FakeDataSource:
    bars = (
        _bar("AAPL", 4, 100.0),
        _bar("AAPL", 0, 116.0),
        _bar("MSFT", 6, 100.0),
        _bar("MSFT", 0, 110.0),
    )
    return FakeDataSource(bars=bars, vix=12.0)


def main() -> None:
    """Start the system once and print the graph-pull cascade."""
    parser = argparse.ArgumentParser(description="graph-pull pipeline demonstrator")
    parser.add_argument(
        "--trace",
        action="store_true",
        help="print per-stage batch metrics after the cascade",
    )
    parser.add_argument(
        "--observe",
        action="store_true",
        help="print the pipeline observatory (stage outputs + floor/ceiling WARNs)",
    )
    parser.add_argument(
        "--run-id",
        default="local-1",
        metavar="ID",
        help="RunRequest id (use a fresh id per run; the graph is append-only)",
    )
    args = parser.parse_args()

    graph = InMemoryGraphStore()
    settings = ProviderSettings(max_staleness_days=7)
    source = _fake_source()
    tickers = _TICKERS_DEMO
    print("MODE: demo  (in-memory + fake data)")

    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=settings,
    )

    print("\nPRE-FLIGHT")
    checks = preflight(graph, source=source, tickers=tickers)
    for check in checks:
        mark = "OK " if check.ok else "XX "
        print(f"  [{mark}] {check.name:<24} {check.detail}")
    if not all_passed(checks):
        print("\nPre-flight failed — not starting.")
        return

    print("\nDISPATCHER")
    place_run_request(graph, run_id=args.run_id, tickers=tickers)
    print(f"  placed RunRequest run-request:{args.run_id} ({len(tickers)} tickers)")

    print("\nCASCADE (one graph-pull pass per agent)")
    for result in cascade_once(graph, provider_agent=agent, broker=PaperBroker()):
        woke = "woke" if result.processed else "idle"
        print(f"  {result.name:<18} {woke}: processed {result.processed}")

    print("\nGRAPH (provenance chain)")
    for label in _CHAIN:
        print(f"  {label:<14} {len(graph.list_nodes(label))}")

    if args.trace:
        from orchestration.batch_trace import print_trace

        print_trace(graph, args.run_id)

    if args.observe:
        from orchestration.packs.trading_observatory import inspect

        print("\nOBSERVATORY")
        print(inspect(graph, args.run_id))


if __name__ == "__main__":
    main()
