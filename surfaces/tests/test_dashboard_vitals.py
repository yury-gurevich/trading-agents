"""Dashboard vitals and UTC window tests.

Agent: surfaces
Role: prove status-line summaries, degraded feeds, pending flags, and schedule math.
External I/O: none; graph is in-memory and AzureReader is fake.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.dashboard.projections_vitals import vitals_projection
from surfaces.dashboard.time_windows import latest_window, next_fire, run_window
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_costs import _settings


def test_vitals_reflect_pending_flags_feeds_images_and_cost() -> None:
    graph = InMemoryGraphStore()
    run = place_run_request(graph, run_id="vitals", tickers=("AAPL",))
    market = graph.merge_node(
        "MarketData",
        "market:vitals",
        {
            "snapshot": {
                "quality": {
                    "notes": [
                        "news_degraded",
                        "fundamentals_degraded",
                        "not-a-feed",
                    ]
                }
            }
        },
    )
    graph.add_edge(run, market, "INGESTED_BY")
    graph.merge_node(
        "Flag", "pending", {"status": "pending", "subject_ref": "s", "severity": "warn"}
    )
    graph.merge_node(
        "Flag",
        "answered",
        {"status": "pending", "subject_ref": "done", "severity": "critical"},
    )
    graph.merge_node(
        "FlagResolution", "res", {"subject_ref": "done", "severity": "critical"}
    )
    graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"created_at": "2026-07-10T00:00:00Z", "holdings": []},
    )
    result = vitals_projection(
        graph,
        FakeAzureReader(),
        _settings(),
        "vitals",
        now=datetime(2026, 7, 10, 12, tzinfo=UTC),
    )
    assert result["pending_flags"] == 1
    assert cast("dict[str, Any]", result["degraded_feeds"])["count"] == 2
    assert cast("dict[str, Any]", result["images"])["status"] == "observed"
    assert cast("dict[str, Any]", result["mtd_cost"])["hardware"] == 7.29


def test_vitals_without_runs_or_azure_are_explicitly_partial() -> None:
    result = vitals_projection(
        InMemoryGraphStore(),
        None,
        _settings(),
        None,
        now=datetime(2026, 7, 10, 12, tzinfo=UTC),
    )
    assert result["run_id"] == ""
    assert cast("dict[str, Any]", result["broker_graph"])["status"] == "unavailable"
    assert cast("dict[str, Any]", result["images"])["status"] == "unavailable"
    assert cast("dict[str, Any]", result["mtd_cost"])["status"] == "partial"
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="no-snapshot", tickers=("AAPL",))
    no_snapshot = vitals_projection(graph, None, _settings(), "no-snapshot")
    assert cast("dict[str, Any]", no_snapshot["broker_graph"])["rows"] == 0


class UsdCostReader(FakeAzureReader):
    def query_costs(self, scope: str, month_to_date: bool) -> list[dict[str, object]]:
        rows = super().query_costs(scope, month_to_date)
        for row in rows:
            row["currency"] = "USD"
        return rows


def test_vitals_do_not_add_usd_hardware_to_aud_llm() -> None:
    result = vitals_projection(
        InMemoryGraphStore(),
        UsdCostReader(),
        _settings(),
        None,
        now=datetime(2026, 7, 10, 12, tzinfo=UTC),
    )
    cost = cast("dict[str, Any]", result["mtd_cost"])
    assert cost["status"] == "split_currency"
    assert cost["total"] is None
    assert cost["hardware_currency"] == "USD"
    assert cost["llm_currency"] == "AUD"


def test_utc_windows_cross_midnight_and_validate_settings() -> None:
    settings = _settings()
    start, end = run_window("2026-07-09", settings)
    assert start.isoformat() == "2026-07-09T22:25:00+00:00"
    assert end.isoformat() == "2026-07-10T00:30:00+00:00"
    before = datetime(2026, 7, 10, 12, tzinfo=UTC)
    assert latest_window(settings, before)[0].date().isoformat() == "2026-07-09"
    after = datetime(2026, 7, 10, 23, tzinfo=UTC)
    assert latest_window(settings, after)[0].date().isoformat() == "2026-07-10"
    assert next_fire(settings, before).startswith("2026-07-10T22:30")
    assert next_fire(settings, after).startswith("2026-07-11T22:30")
    bad = settings.model_copy(update={"master_window_start_utc": "bad"})
    with pytest.raises(ValueError, match="expected HH:MM"):
        run_window("2026-07-09", bad)
    seconds = settings.model_copy(update={"master_window_start_utc": "22:25:01"})
    with pytest.raises(ValueError, match="expected HH:MM"):
        run_window("2026-07-09", seconds)
    same_day = settings.model_copy(update={"window_end_utc": "23:30"})
    assert run_window("2026-07-09", same_day)[1].date().isoformat() == "2026-07-09"
