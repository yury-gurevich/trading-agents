"""Stop/target comparison report tests.

Agent: tooling
Role: prove the S150 comparison script is read-only and reports both modes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.compare_stop_targets import compare_stop_targets, render_report

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from kernel import Node


def test_comparison_script_reports_both_modes_and_touch_difference() -> None:
    """ANLZ-OBS-01 / ADR-0013: report exposes flat vs scaled stop outcomes."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Recommendation",
        "analyst-run:MRVL",
        _recommendation_props(flat=0.05, scaled=0.08, drawdown=0.06),
    )
    graph.merge_node(
        "Recommendation",
        "analyst-run:BAC",
        _recommendation_props(flat=0.05, scaled=0.042, drawdown=0.03),
    )

    report = render_report(compare_stop_targets(graph, run_ids=("analyst-run",)))

    assert "mode\trecommendations\tstop_min_pct\tstop_median_pct" in report
    assert "flat\t2\t5.00\t5.00\t5.00\t100.00\t2\t50.00" in report
    assert "scaled\t2\t4.20\t6.10\t8.00\t100.00\t2\t0.00" in report


def test_comparison_script_never_writes_or_promotes() -> None:
    """ANLZ-NEV-01 / ADR-0013: comparison is read-only and never flips settings."""
    graph = ReadOnlyGraph()

    report = compare_stop_targets(graph)

    assert [row.mode for row in report] == ["flat", "scaled"]
    assert graph.writes == []


class ReadOnlyGraph(InMemoryGraphStore):
    """Graph fake that records any attempted write."""

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[str] = []
        self._merge_node(
            "Recommendation",
            "analyst-run:MRVL",
            _recommendation_props(flat=0.05, scaled=0.08, drawdown=0.06),
            schema_version=1,
        )

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, Any],
        *,
        schema_version: int = 1,
    ) -> Node:
        self.writes.append(f"{label}:{key}")
        raise AssertionError("comparison script must not write")


def _recommendation_props(
    *, flat: float, scaled: float, drawdown: float
) -> dict[str, object]:
    return {
        "ticker": "MRVL",
        "action": "buy",
        "stop_target_flat_stop_pct": flat,
        "stop_target_flat_target_pct": flat * 2,
        "stop_target_scaled_stop_pct": scaled,
        "stop_target_scaled_target_pct": scaled * 2,
        "stop_target_observed_drawdown_pct": drawdown,
    }
