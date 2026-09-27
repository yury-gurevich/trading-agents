"""Fleet-produced live graphs for the S237 fidelity tests.

Agent: tooling
Role: run the fleet's own graph-pull stages on synthetic inputs, so every live output
      an export carries was decided by the fleet and none was written by a test.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.replay_settings import build_effective_settings
from tests.fidelity_fleet_data import HELD_ONLY, TICKERS, close, market_data, regime

from agents.analyst.poll import analyze_scan_node
from agents.execution.broker import BrokerAccount, BrokerPosition
from agents.execution.reconciliation_store import write_snapshot
from agents.monitor.position_sync import sync_positions_snapshot
from agents.monitor.settings import MonitorSettings
from agents.portfolio_manager.issuer_map import load_issuer_map
from agents.portfolio_manager.poll import evaluate_analyst_node

# The provider's own node writers, so the MarketData/RegimeContext shape is live's.
from agents.provider.ingest import _write_market_data, _write_regime_context
from agents.scanner.poll import scan_market_node
from contracts.common import Window
from contracts.position_sync import SNAPSHOT_REFRESH_EDGE
from kernel import CollectingFaultSink
from kernel.graph_memory import InMemoryGraphStore
from orchestration.deploy_record import record_deploy
from orchestration.resume import resume_run
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from kernel import GraphStore, Node

ROOT = Path(__file__).resolve().parents[1]
ISSUER_MAP = ROOT / "orchestration" / "packs" / "trading_issuer_map.json"
SETTINGS = build_effective_settings(())
DEPLOYED_AT = datetime(2026, 9, 1, tzinfo=UTC)
EQUITY_CENTS = 100_000_000
# ticker, quantity, average entry cents: both held names are Banks, and the book is
# deployed above the PM's derived floor, so the sector cap evaluates (PM-NEV-06).
HOLDINGS = (("T03", 2_000, 2_600), (HELD_ONLY, 1_000, 7_000))


@dataclass(frozen=True)
class FleetDay:
    """One run to drive through the fleet's graph-pull stages."""

    session: date
    holdings: tuple[tuple[str, int, int], ...] = HOLDINGS
    benchmark: bool = True
    enriched: bool = True
    volume_share: float = 1.0
    run_id: str | None = None
    through_pm: bool = True
    fresh_account: bool = True
    stale_book: bool = False


def fleet_graph(
    days: tuple[FleetDay, ...], *, git_sha: str, graph: InMemoryGraphStore | None = None
) -> InMemoryGraphStore:
    """Return a graph holding one deploy and every day's live run."""
    store = graph if graph is not None else InMemoryGraphStore()
    record_deploy(
        store,
        tag="s-fixture",
        git_sha=git_sha,
        actor="fixture",
        deployed_at=DEPLOYED_AT,
    )
    for day in days:
        run_fleet_day(store, day)
    return store


def run_fleet_day(graph: GraphStore, day: FleetDay) -> str:
    """Run one session exactly as the graph-pull fleet runs it; return its run id."""
    run_id = day.run_id or f"sched-{day.session.isoformat()}"
    request = place_run_request(
        graph, run_id=run_id, tickers=TICKERS, as_of=day.session
    )
    snapshot = write_snapshot(
        graph,
        run_id=run_id,
        holdings=() if day.stale_book else _positions(day),
        account=_account() if day.fresh_account and not day.stale_book else None,
        status="stale" if day.stale_book else "fresh",
        stale_reason="broker unreachable" if day.stale_book else None,
    )
    graph.add_edge(request, snapshot, SNAPSHOT_REFRESH_EDGE)
    sync_positions_snapshot(snapshot, graph=graph, settings=MonitorSettings())
    universe = tuple(dict.fromkeys((*TICKERS, *(row[0] for row in day.holdings))))
    window = Window(start=day.session - timedelta(days=400), end=day.session)
    market = market_data(
        run_id,
        day.session,
        universe,
        benchmark=day.benchmark,
        enriched=day.enriched,
        volume_share=day.volume_share,
    )
    _write_market_data(graph, market, universe, window, run_id)
    _write_regime_context(graph, regime(run_id, day.session), window, run_id)
    market_node = graph.get_node("MarketData", f"market-data:{run_id}")
    assert market_node is not None
    graph.add_edge(request, market_node, "INGESTED_BY")
    scan_market_node(market_node, graph=graph, settings=SETTINGS.scanner)
    if day.through_pm:
        run_downstream(graph, child(graph, market_node, "SCANNED_BY"))
    return run_id


def run_downstream(graph: GraphStore, scan: Node) -> Node:
    """Run the analyst and the PM on one ScanRun; return the PMRun."""
    analyze_scan_node(
        scan, graph=graph, settings=SETTINGS.analyst, sink=CollectingFaultSink()
    )
    analyst = child(graph, scan, "ANALYZED_BY")
    evaluate_analyst_node(
        analyst,
        graph=graph,
        settings=SETTINGS.portfolio,
        issuer_map=load_issuer_map(str(ISSUER_MAP)),
        sink=CollectingFaultSink(),
    )
    return child(graph, analyst, "EVALUATED_BY")


def resume_from_analyst(graph: GraphStore, run_id: str) -> Node:
    """Resume a run that stopped after its scan, as orchestration does; finish it."""
    placement = resume_run(graph, source_run_id=run_id, resume_from="analyst")
    request = graph.get_node("RunRequest", placement.node_key)
    assert request is not None
    market = child(graph, request, "INGESTED_BY")
    return run_downstream(graph, child(graph, market, "SCANNED_BY"))


def pm_node(graph: GraphStore, run_id: str) -> Node:
    """Return the PMRun a fleet day produced."""
    market = graph.get_node("MarketData", f"market-data:{run_id}")
    assert market is not None
    scan = child(graph, market, "SCANNED_BY")
    return child(graph, child(graph, scan, "ANALYZED_BY"), "EVALUATED_BY")


def child(graph: GraphStore, node: Node, edge: str) -> Node:
    """Return the one child of ``node`` over ``edge``."""
    children = list(graph.descendants(node, max_depth=1, edge_types={edge}))
    assert len(children) == 1, (node.key, edge, len(children))
    return children[0]


def _account() -> BrokerAccount:
    return BrokerAccount(
        cash_cents=EQUITY_CENTS // 2,
        equity_cents=EQUITY_CENTS,
        buying_power_cents=EQUITY_CENTS // 2,
    )


def _positions(day: FleetDay) -> tuple[BrokerPosition, ...]:
    return tuple(
        BrokerPosition(
            ticker=ticker,
            quantity=quantity,
            avg_entry_cents=entry,
            market_value_cents=round(quantity * close(ticker, day.session) * 100),
        )
        for ticker, quantity, entry in day.holdings
    )
