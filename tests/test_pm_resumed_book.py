"""S240 a run placed by resume_run weighs its book at the run it resumes.

Agent: tooling
Role: prove, on a child placed by the real resume primitive, that the PM reads the
      source run's snapshot, and name the one reader that does not follow yet.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import TYPE_CHECKING

from scripts.replay_fidelity_inputs import load_session
from scripts.replay_settings import build_effective_settings
from tests.fidelity_fleet import EQUITY_CENTS, FleetDay, child, fleet_graph
from tests.fidelity_fleet_data import SESSIONS
from tests.fidelity_harness import export

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from orchestration.resume import resume_run

if TYPE_CHECKING:
    from pathlib import Path

    from agents.portfolio_manager.portfolio import PortfolioState
    from kernel.graph_memory import InMemoryGraphStore

SECOND = f"sched-{SESSIONS[1].isoformat()}"
SEED = build_effective_settings(()).portfolio.starting_cash


def _stalled_then_resumed() -> tuple[InMemoryGraphStore, str]:
    """A session that stopped after its scan, resumed as orchestration resumes it."""
    graph = fleet_graph(
        (FleetDay(SESSIONS[0]), FleetDay(SESSIONS[1], through_pm=False)),
        git_sha="abc123",
    )
    placement = resume_run(graph, source_run_id=SECOND, resume_from="analyst")
    request = graph.get_node("RunRequest", placement.node_key)
    assert request is not None
    market = child(graph, request, "INGESTED_BY")
    # The PM poll takes the run id from the MarketData it reads (poll.py), the clone's.
    return graph, str(market.props["run_id"])


def _marks(graph: InMemoryGraphStore, run_id: str) -> dict[str, Decimal]:
    snapshot = next(
        node
        for node in graph.list_nodes("BrokerPositionSnapshot")
        if node.props["run_id"] == run_id
    )
    return {
        item["ticker"]: Decimal(item["market_value_cents"]) / 100
        for item in snapshot.props["holdings"]
    }


def _amounts(portfolio: PortfolioState) -> dict[str, Decimal]:
    return {ticker: money.amount for ticker, money in portfolio.position_values.items()}


def test_a_child_placed_by_resume_run_reads_its_sources_snapshot() -> None:
    """PM-IN-05 / PM-IDN-01: the resumed PM sizes on the source's book, not the seed."""
    graph, child_run_id = _stalled_then_resumed()
    assert child_run_id == f"{SECOND}-resume-analyst"
    assert not [
        node
        for node in graph.list_nodes("BrokerPositionSnapshot")
        if node.props["run_id"] == child_run_id
    ]

    live = portfolio_from_graph(graph, SEED, run_id=child_run_id)

    assert live.cash.amount == Decimal(EQUITY_CENTS) / 100
    assert live.cash.amount != SEED
    assert live.account_equity_cents == EQUITY_CENTS
    assert _amounts(live) == _marks(graph, SECOND)


def test_the_export_does_not_follow_a_resumed_sessions_lineage_yet(
    tmp_path: Path,
) -> None:
    """PM-IN-05 / DL-242: the export's book for a resumed session is still empty.

    A witness, not a guarantee: the fidelity export picks the book by the clone's
    run id, so its replay seeds from starting_cash while live reads the source's
    snapshot, and it says so by naming `held_positions` as not persisted. Fixing
    the export is out of S240's scope (the spec forbids editing it).
    """
    graph, child_run_id = _stalled_then_resumed()
    live = portfolio_from_graph(graph, SEED, run_id=child_run_id)
    export_dir = export(graph, tmp_path / "export")
    payload = json.loads((export_dir / f"{SECOND}.json").read_text(encoding="utf-8"))

    inputs = load_session(export_dir / f"{SECOND}.json")

    assert payload["book"] == {}
    assert "held_positions" in payload["not_persisted"]
    assert inputs.portfolio.cash.amount == SEED
    assert inputs.portfolio.cash != live.cash
