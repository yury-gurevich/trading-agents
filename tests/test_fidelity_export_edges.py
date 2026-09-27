"""S237 export edges: empty runs, deploy choice, a benchmark never stored, lost lots.

Agent: tooling
Role: prove every fail-closed branch of the exporter names what it could not read.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from scripts.fidelity_export_helpers import jsonable, parse_dt
from scripts.fidelity_export_outcomes import benchmark_gap
from scripts.fidelity_exporter import export_sessions
from tests.fidelity_fleet import FleetDay, child, fleet_graph, run_fleet_day
from tests.fidelity_fleet_data import SESSIONS, TICKERS, market_data
from tests.fidelity_harness import replay, rows, tiny_repo

from agents.provider.ingest import _write_market_data
from contracts.common import Window
from contracts.positions import open_positions
from kernel.graph_memory import InMemoryGraphStore
from orchestration.deploy_record import record_deploy
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from pathlib import Path

FIRST, SECOND, THIRD = (f"sched-{day.isoformat()}" for day in SESSIONS[:3])
LATER = datetime(2099, 1, 1, tzinfo=UTC)


def _export(graph: InMemoryGraphStore, out: Path) -> dict[str, dict[str, Any]]:
    paths = export_sessions(graph, start=SESSIONS[0], end=SESSIONS[-1], out=out)
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in paths}


def test_a_run_that_stored_nothing_is_exported_empty_and_compares_nothing(
    tmp_path: Path,
) -> None:
    """SCAN-OBS-01 / RPT-NEV-02: a run with no stage output is empty, not invented."""
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id=FIRST, tickers=TICKERS, as_of=SESSIONS[0])
    request = place_run_request(
        graph, run_id=SECOND, tickers=TICKERS, as_of=SESSIONS[1]
    )
    window = Window(start=SESSIONS[1] - timedelta(days=400), end=SESSIONS[1])
    market = market_data(SECOND, SESSIONS[1], TICKERS)
    _write_market_data(graph, market, TICKERS, window, SECOND)
    ingested = graph.get_node("MarketData", f"market-data:{SECOND}")
    assert ingested is not None
    graph.add_edge(request, ingested, "INGESTED_BY")

    sessions = _export(graph, tmp_path / "export")

    empty = sessions[FIRST]
    blocks = ("market", "regime", "book", "scanner", "analyst", "pm", "deploy")
    assert all(empty[name] == {} for name in blocks)
    assert empty["not_persisted"] == [
        "active_broker_stop_refs",
        "held_positions",
        "held_stops",
    ]
    ingested_only = sessions[SECOND]
    assert ingested_only["market"]["tickers"] == list(TICKERS)
    assert (ingested_only["regime"], ingested_only["scanner"]) == ({}, {})
    repo, _sha = tiny_repo(tmp_path / "repo")
    summary = replay(tmp_path / "export", tmp_path / "out", repo)
    assert rows(tmp_path / "out") == []
    assert summary["replayed"] == {"scanner": 0, "analyst": 0, "pm": 0}
    assert summary["verdict"] == "INSUFFICIENT"


def test_the_deploy_is_the_latest_readable_record_at_or_before_the_scan(
    tmp_path: Path,
) -> None:
    """ANLZ-OBS-01: a later or unreadable DeployRecord is never the one in force."""
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha="a" * 40)
    record_deploy(
        graph, tag="s-later", git_sha="b" * 40, actor="fixture", deployed_at=LATER
    )
    graph.merge_node(
        "DeployRecord",
        "deploy:unreadable",
        {"tag": "s-bad", "git_sha": "c" * 40, "deployed_at": "not a time"},
    )
    later_only = InMemoryGraphStore()
    record_deploy(
        later_only, tag="s-later", git_sha="b" * 40, actor="fixture", deployed_at=LATER
    )
    run_fleet_day(later_only, FleetDay(SESSIONS[0]))

    assert _export(graph, tmp_path / "a")[FIRST]["deploy"]["git_sha"] == "a" * 40
    assert _export(later_only, tmp_path / "b")[FIRST]["deploy"] == {}


def test_the_export_names_a_benchmark_live_used_but_never_stored(
    tmp_path: Path,
) -> None:
    """SCAN-OUT-06: a scan with beta over a snapshot without SPY is a named gap."""
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha="a" * 40)
    stored = graph.get_node("MarketData", f"market-data:{FIRST}")
    assert stored is not None
    props = jsonable(stored.props)
    assert isinstance(props, dict)
    request = place_run_request(
        graph, run_id=SECOND, tickers=TICKERS, as_of=SESSIONS[1]
    )
    unstored = graph.merge_node(
        "MarketData",
        f"market-data:{SECOND}",
        {**props, "snapshot": {**props["snapshot"], "benchmark": []}, "run_id": SECOND},
    )
    graph.add_edge(request, unstored, "INGESTED_BY")
    graph.add_edge(unstored, child(graph, stored, "SCANNED_BY"), "SCANNED_BY")

    sessions = _export(graph, tmp_path / "export")

    assert "benchmark" not in sessions[FIRST]["not_persisted"]
    assert "benchmark" in sessions[SECOND]["not_persisted"]


def test_a_lot_that_returns_after_it_was_superseded_is_named_not_guessed(
    tmp_path: Path,
) -> None:
    """PM-IDN-01: a holding with no single active Position is held_positions."""
    lot, other = (("T03", 2_000, 2_600),), (("T03", 2_500, 2_700),)
    graph = fleet_graph(
        (
            FleetDay(SESSIONS[0], holdings=lot),
            FleetDay(SESSIONS[1], holdings=other),
            FleetDay(SESSIONS[2], holdings=lot),
        ),
        git_sha="a" * 40,
    )

    third = _export(graph, tmp_path / "export")[THIRD]

    assert "T03" not in {position.ticker for position in open_positions(graph)}
    assert third["positions"] == []
    assert "held_positions" in third["not_persisted"]


def test_projection_helpers_keep_json_safe_and_fail_closed() -> None:
    """RPT-NEV-02 / SCAN-OUT-06: ISO dates; no time and no evidence read as none."""
    assert jsonable({"day": date(2026, 9, 28), "tags": frozenset({"b", "a"})}) == {
        "day": "2026-09-28",
        "tags": ["a", "b"],
    }
    assert parse_dt("not a time") is None
    assert parse_dt(None) is None
    assert benchmark_gap({"benchmark": []}, {}, {}) is False
    assert parse_dt("2026-09-28T22:30:00") == datetime(2026, 9, 28, 22, 30, tzinfo=UTC)
