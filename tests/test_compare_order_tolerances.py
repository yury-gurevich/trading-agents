"""Order tolerance comparison report tests.

Agent: tooling
Role: prove the S149 comparison script is read-only and reports both modes.
External I/O: none.
"""

from __future__ import annotations

from scripts.compare_order_tolerances import compare_order_tolerances, render_report

from kernel import InMemoryGraphStore


def test_comparison_script_reports_both_modes_when_limits_differ() -> None:
    """EXEC-OBS-01 / ADR-0013: report exposes flat vs scaled fill differences."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Fill",
        "pm-run:AMD:buy",
        _fill_props(
            side="buy",
            decided=10000,
            actual=10120,
            flat_limit=10050,
            scaled_limit=10150,
        ),
    )
    graph.merge_node(
        "Fill",
        "pm-run:SCHW:buy",
        _fill_props(
            side="buy",
            decided=10000,
            actual=10040,
            flat_limit=10050,
            scaled_limit=10040,
        ),
    )

    report = render_report(compare_order_tolerances(graph, run_ids=("pm-run",)))

    assert "mode\torders\twould_have_filled\tdrop_rate_pct\tavg_slippage_bps" in report
    assert "flat\t2\t1\t50.00\t40.00" in report
    assert "scaled\t2\t2\t0.00\t80.00" in report


def test_comparison_script_never_writes_or_promotes() -> None:
    """EXEC-NEV-01 / ADR-0013: comparison is read-only and never flips settings."""
    graph = ReadOnlyGraph()

    report = compare_order_tolerances(graph)

    assert [row.mode for row in report] == ["flat", "scaled"]
    assert graph.writes == []


class ReadOnlyGraph(InMemoryGraphStore):
    """Graph fake that records any attempted write."""

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[str] = []
        self._merge_node(
            "Fill",
            "pm-run:AMD:buy",
            _fill_props(
                side="buy",
                decided=10000,
                actual=10120,
                flat_limit=10050,
                scaled_limit=10150,
            ),
            schema_version=1,
        )

    def merge_node(
        self, label: str, key: str, props: dict[str, object], *, schema_version: int = 1
    ):
        self.writes.append(f"{label}:{key}")
        raise AssertionError("comparison script must not write")


def _fill_props(
    *,
    side: str,
    decided: int,
    actual: int,
    flat_limit: int,
    scaled_limit: int,
) -> dict[str, object]:
    return {
        "source_run_id": "pm-run",
        "side": side,
        "price_cents": actual,
        "order_decided_price_cents": decided,
        "order_flat_limit_price_cents": flat_limit,
        "order_scaled_limit_price_cents": scaled_limit,
    }
