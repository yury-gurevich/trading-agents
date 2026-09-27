"""Tests for S237 live fidelity export.

Agent: tooling
Role: prove the exporter is read-only, scheduled-only, and out-of-worktree.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from scripts.fidelity_exporter import export_sessions, refuse_worktree_out

from kernel.graph_memory import InMemoryGraphStore


class TrackingGraph(InMemoryGraphStore):
    def __init__(self) -> None:
        super().__init__()
        self.write_count = 0

    def merge_node(self, *args: object, **kwargs: object) -> object:
        self.write_count += 1
        return super().merge_node(*args, **kwargs)  # type: ignore[arg-type]

    def add_edge(self, *args: object, **kwargs: object) -> None:
        self.write_count += 1
        super().add_edge(*args, **kwargs)  # type: ignore[arg-type]


def test_export_reads_only_sched_runs_and_follows_linked_stage(tmp_path: Path) -> None:
    """SCAN-OBS-01 / ANLZ-OBS-01 / PM-OBS-01: export is graph read-only."""
    graph = TrackingGraph()
    run = graph.merge_node(
        "RunRequest", "request:sched-2026-09-25", {"run_id": "sched-2026-09-25"}
    )
    graph.merge_node(
        "RunRequest", "request:manual-2026-09-25", {"run_id": "manual-2026-09-25"}
    )
    market = graph.merge_node(
        "MarketData",
        "market-data:sched-2026-09-25",
        {
            "run_id": "sched-2026-09-25",
            "snapshot": {"bars": [], "benchmark": []},
        },
    )
    graph.merge_node(
        "ScanRun",
        "scan-old",
        {"candidate_set": {"candidates": [{"ticker": "AAA", "rank": 1}]}},
    )
    scan = graph.merge_node(
        "ScanRun",
        "scan-resume",
        {
            "linked_from_key": "scan-old",
            "created_at": "2026-09-25T22:30:00+00:00",
        },
    )
    graph.merge_node(
        "AnalystRun", "analyst-old", {"recommendation_set": {"recommendations": []}}
    )
    analyst = graph.merge_node(
        "AnalystRun",
        "analyst-resume",
        {"linked_from_key": "analyst-old", "recommendation_set": {"bad": True}},
    )
    pm = graph.merge_node(
        "PMRun", "pm-live", {"created_at": "2026-09-25T22:40:00+00:00"}
    )
    broker = graph.merge_node(
        "BrokerPositionSnapshot",
        "broker:sched-2026-09-25",
        {
            "run_id": "sched-2026-09-25",
            "holdings": [{"ticker": "AAA", "market_value_cents": 12345}],
        },
    )
    graph.merge_node(
        "DeployRecord",
        "deploy:s232",
        {"deployed_at": "2026-09-25T21:00:00+00:00", "tag": "s232", "sha": "abc123"},
    )
    graph.add_edge(run, market, "INGESTED_BY")
    graph.add_edge(market, scan, "SCANNED_BY")
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    graph.add_edge(run, broker, "REFRESHES")
    graph.write_count = 0

    written = export_sessions(
        graph,
        start=date(2026, 9, 25),
        end=date(2026, 9, 25),
        out=tmp_path,
    )

    assert graph.write_count == 0
    assert len(written) == 1
    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert payload["run_id"] == "sched-2026-09-25"
    assert payload["resumed"] is True
    assert payload["scanner"]["key"] == "scan-old"
    assert payload["analyst"]["key"] == "analyst-old"
    assert payload["book"]["holdings"][0]["market_value_cents"] == 12345
    assert payload["deploy"]["sha"] == "abc123"
    assert "benchmark" in payload["not_persisted"]


def test_export_refuses_out_inside_repo(tmp_path: Path) -> None:
    """RPT-NEV-02: vendor/live export data is never written into the worktree."""
    del tmp_path
    with pytest.raises(ValueError, match="inside the worktree"):
        refuse_worktree_out(Path.cwd() / "fidelity-export")
