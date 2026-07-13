"""Dashboard run projections tests.

Agent: surfaces
Role: verify runs list ordering, verdict projection (PASS, no-trade FAIL,
      generic FAIL), and per-stage check outcomes over a real cascade.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, cast

import surfaces.dashboard.projections as proj
from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.observatory import Breach
from orchestration.packs.trading_acceptance import TradingAcceptanceResult
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    import pytest


def cascade_graph(run_id: str = "dash-ok") -> InMemoryGraphStore:
    """A full clean in-process run — the PASS fixture."""
    graph = InMemoryGraphStore()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id=run_id, tickers=("AAPL", "MSFT"))
    list(cascade_once(graph, provider_agent=agent, broker=PaperBroker()))
    return graph


def test_list_runs_newest_first() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="old", tickers=("AAPL",), as_of=date(2026, 7, 1))
    place_run_request(graph, run_id="new", tickers=("AAPL",), as_of=date(2026, 7, 9))
    rows = proj.list_runs(graph)
    assert [r["run_id"] for r in rows] == ["new", "old"]
    assert rows[0]["requested_at"] == "2026-07-09"


def test_run_request_node_lookup() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="here", tickers=("AAPL",))
    assert proj.run_request_node(graph, "here") is not None
    assert proj.run_request_node(graph, "missing") is None


def test_verdict_pass_on_clean_cascade() -> None:
    graph = cascade_graph()
    verdict = proj.run_verdict(graph, "dash-ok")
    assert verdict["passed"] is True
    assert verdict["no_trade_day"] is False
    assert verdict["annotation"] is None


def test_verdict_fail_on_broken_chain_is_not_no_trade() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="partial", tickers=("AAPL",))
    verdict = proj.run_verdict(graph, "partial")
    assert verdict["passed"] is False
    assert verdict["no_trade_day"] is False
    breaches = cast("list[dict[str, Any]]", verdict["breaches"])
    assert any(b["detail"] == "NOT REACHED" for b in breaches)


def test_stages_shape_on_clean_cascade() -> None:
    stages = proj.run_stages(cascade_graph(), "dash-ok")
    assert [s["name"] for s in stages] == [
        "provider",
        "scanner",
        "analyst",
        "pm",
        "execution",
        "monitor",
        "reporter",
    ]
    provider = stages[0]
    assert provider["reached"] is True
    checks = provider["checks"]
    assert isinstance(checks, list)
    assert checks
    assert all({"key", "kind", "severity", "ok", "detail"} <= set(c) for c in checks)
    ok_returned = next(c for c in checks if c["key"] == "returned")
    assert ok_returned["ok"] is True
    assert ok_returned["detail"] is None


def test_unreached_stage_projects_as_not_reached() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="partial", tickers=("AAPL",))
    stages = proj.run_stages(graph, "partial")
    assert all(s["reached"] is False for s in stages)
    assert stages[0]["checks"] == []


def _no_trade_result() -> TradingAcceptanceResult:
    return TradingAcceptanceResult(
        verdict="NO_TRADE",
        breaches=(
            Breach("analyst", "scored", "0 < floor 1.0"),
            Breach("pm", "evaluated", "0 < floor 1.0"),
            Breach("provider", "sector_coverage", "0 < floor 1.0", severity="warn"),
        ),
    )


def _graph_with_rejections(rejected: int) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="quiet", tickers=("AAPL",))
    rec_set = {
        "run_id": "quiet",
        "as_of": "2026-07-09",
        "recommendations": [],
        "rejections": [
            {
                "ticker": f"T{i}",
                "reason": "confidence 0.527 below regime floor 0.600",
            }
            for i in range(rejected)
        ],
    }
    graph.merge_node("AnalystRun", "analyst-run:quiet", {"recommendation_set": rec_set})
    return graph


def test_no_trade_day_annotated(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = _graph_with_rejections(5)
    monkeypatch.setattr(proj, "accept_run", lambda g, r: _no_trade_result())
    monkeypatch.setattr(
        proj,
        "walk_chain",
        lambda g, r: {"AnalystRun": g.get_node("AnalystRun", "analyst-run:quiet")},
    )
    verdict = proj.run_verdict(graph, "quiet")
    assert verdict["no_trade_day"] is True
    assert verdict["confidence_bar"] == 0.6
    assert "completed normally" in str(verdict["annotation"])
    assert "All 5 candidates" in str(verdict["annotation"])


def test_rejection_count_handles_missing_node_and_props() -> None:
    graph = InMemoryGraphStore()
    assert proj._rejection_count(graph, "nope") == 0
    graph.merge_node("AnalystRun", "analyst-run:bare", {"other": 1})
    node = graph.get_node("AnalystRun", "analyst-run:bare")
    assert node is not None
    assert proj._rejection_count(graph, "bare") == 0
