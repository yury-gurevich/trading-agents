"""Local end-to-end demonstrator for the graph-pull pipeline.

Agent: tooling
Role: start the system in one process — pre-flight checks, the dispatcher places ONE
      RunRequest, then run each agent's graph-pull poll once and print how every
      downstream agent wakes off its prerequisite gate
      (provider → scanner → analyst → PM → execution → monitor → reporter).
      --real: loads .env, uses PostgreSQL (POSTGRES_DSN) + real Tiingo OHLCV data.
      --universe FILE: newline-delimited tickers; overrides the built-in list.
      Default: in-memory graph + FakeDataSource (no credentials needed).
External I/O: stdout; network (Tiingo, Finnhub, PostgreSQL) when --real.

Run it:
  PYTHONPATH=. python scripts/run_local.py           # in-memory demo
  PYTHONPATH=. python scripts/run_local.py --real    # live Postgres + real market data
  PYTHONPATH=. python scripts/run_local.py --real --universe scripts/universe_sp100.txt
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta

from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.scanner.universe import load_universe_file
from contracts.provider import OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import all_passed, place_run_request, preflight

_TICKERS_DEMO: tuple[str, ...] = ("AAPL", "MSFT")
_TICKERS_REAL: tuple[str, ...] = ("AAPL", "MSFT", "GOOGL")
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
        "--real",
        action="store_true",
        help="use live PostgreSQL (POSTGRES_DSN from .env) + real Tiingo market data",
    )
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
        "--universe",
        metavar="FILE",
        help="newline-delimited ticker file; overrides the built-in universe",
    )
    parser.add_argument(
        "--run-id",
        default="local-1",
        metavar="ID",
        help="RunRequest id (use a fresh id per run; the graph is append-only)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=0,
        metavar="N",
        help="paced ingest sub-batch size (0 = single-shot); respects API rate limits",
    )
    parser.add_argument(
        "--chunk-delay",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="pause between ingest chunks (with --chunk-size)",
    )
    parser.add_argument(
        "--ohlcv-only",
        action="store_true",
        help="fast mode (DL-29): request only OHLCV; skip per-ticker Finnhub "
        "enrichment the acceptance gate doesn't need (~33 min -> seconds at S&P-500)",
    )
    parser.add_argument(
        "--veto",
        action="store_true",
        help="DL-31 Part B: run the LLM challenger-veto between PM and execution "
        "(real model per .env); persists a DeliberationRun with the debate transcript",
    )
    args = parser.parse_args()

    if args.chunk_size:
        os.environ["PROVIDER_INGEST_CHUNK_SIZE"] = str(args.chunk_size)
        os.environ["PROVIDER_INGEST_CHUNK_DELAY_SECONDS"] = str(args.chunk_delay)

    if args.ohlcv_only:
        os.environ["PROVIDER_INGEST_OHLCV_ONLY"] = "true"

    if args.real:
        from dotenv import load_dotenv

        from agents.provider.composite import market_source_from_settings
        from kernel.graph_env import build_graph_from_env

        load_dotenv()
        graph = build_graph_from_env()
        settings = ProviderSettings()
        source = market_source_from_settings(settings)
        tickers = _TICKERS_REAL
        print("MODE: real  (Postgres + Tiingo/Finnhub)")
    else:
        graph = InMemoryGraphStore()
        settings = ProviderSettings(max_staleness_days=7)
        source = _fake_source()
        tickers = _TICKERS_DEMO
        print("MODE: demo  (in-memory + fake data)")

    if args.universe:
        tickers = load_universe_file(args.universe)
        print(f"UNIVERSE: {args.universe}  ({len(tickers)} tickers)")

    if args.chunk_size:
        print(f"INGEST: chunked  size={args.chunk_size}  delay={args.chunk_delay}s")
    if args.ohlcv_only:
        print("INGEST: OHLCV-only fast mode (enrichment skipped, DL-29)")

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

    deliberation_llm = None
    deliberation_judge_llm = None
    if args.veto:
        from scripts.deliberate import build_role_llms

        deliberation_llm, deliberation_judge_llm = build_role_llms(True)
        print("VETO: LLM challenger-veto active between PM and execution (DL-31)")

    print("\nCASCADE (one graph-pull pass per agent)")
    for result in cascade_once(
        graph,
        provider_agent=agent,
        broker=PaperBroker(),
        deliberation_llm=deliberation_llm,
        deliberation_judge_llm=deliberation_judge_llm,
    ):
        woke = "woke" if result.processed else "idle"
        print(f"  {result.name:<18} {woke}: processed {result.processed}")

    print("\nGRAPH (provenance chain)")
    for label in _CHAIN:
        print(f"  {label:<14} {len(graph.list_nodes(label))}")

    if args.veto:
        for delib in graph.list_nodes("DeliberationRun"):
            print("\nDELIBERATION (persisted on the graph)")
            print(f"  verdicts: {dict(delib.props['verdicts'])}")
            print(f"  vetoed:   {list(delib.props['vetoed_tickers'])}")

    if args.trace:
        from orchestration.batch_trace import print_trace

        print_trace(graph, args.run_id)

    if args.observe:
        from orchestration.packs.trading_observatory import inspect

        print("\nOBSERVATORY")
        print(inspect(graph, args.run_id))


if __name__ == "__main__":
    main()
