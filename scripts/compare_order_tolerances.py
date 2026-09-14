"""Compare flat vs volatility-scaled order tolerance outcomes.

Agent: tooling
Role: report ADR-0013 challenger evidence from persisted Fill records.
External I/O: graph reads when run as a CLI.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Literal

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.order_tolerance_fields import (  # noqa: E402
    actual_price_cents,
    limit_cents,
    price_cents,
    tolerance_row,
)
from scripts.order_tolerance_informativeness import (  # noqa: E402
    Informativeness,
    assess,
    render_comparison_line,
)

if TYPE_CHECKING:
    from kernel import GraphStore, Node

Mode = Literal["flat", "scaled"]

_BPS = Decimal("10000")
_PCT = Decimal("100")
_ONE_CENT = Decimal("0.01")
_MODES: tuple[Mode, ...] = ("flat", "scaled")


@dataclass(frozen=True)
class ModeReport:
    """One mode's counterfactual fill/drop/slippage aggregate."""

    mode: Mode
    order_count: int
    would_have_filled: int
    drop_rate_pct: Decimal
    avg_slippage_bps: Decimal | None


@dataclass(frozen=True)
class ComparisonReport:
    """Both mode aggregates, plus whether they could have differed at all."""

    modes: tuple[ModeReport, ...]
    informativeness: Informativeness


def compare_order_tolerances(
    graph: GraphStore, *, run_ids: tuple[str, ...] = ()
) -> ComparisonReport:
    """Return report rows for fills with S149 tolerance evidence."""
    fills = tuple(_eligible_fills(graph, frozenset(run_ids)))
    return ComparisonReport(
        modes=tuple(_mode_report(mode, fills) for mode in _MODES),
        informativeness=assess(tuple(tolerance_row(node) for node in fills)),
    )


def render_report(report: ComparisonReport) -> str:
    """Render a tab-separated, pasteable operator report."""
    lines = ["mode\torders\twould_have_filled\tdrop_rate_pct\tavg_slippage_bps"]
    lines.extend(
        "\t".join(
            (
                row.mode,
                str(row.order_count),
                str(row.would_have_filled),
                _fmt(row.drop_rate_pct),
                "n/a" if row.avg_slippage_bps is None else _fmt(row.avg_slippage_bps),
            )
        )
        for row in report.modes
    )
    lines.append(render_comparison_line(report.informativeness))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the read-only comparison against the configured graph."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="path to .env")
    parser.add_argument(
        "--run-id",
        action="append",
        default=[],
        help="PM source_run_id to include; repeat for a run window",
    )
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    graph = build_graph_from_env()
    try:
        print(
            render_report(compare_order_tolerances(graph, run_ids=tuple(args.run_id)))
        )
    finally:
        close = getattr(graph, "close", None)
        if close is not None:
            close()
    return 0


def _eligible_fills(graph: GraphStore, run_ids: frozenset[str]) -> tuple[Node, ...]:
    rows: list[Node] = []
    for node in graph.list_nodes("Fill"):
        if run_ids and str(node.props.get("source_run_id", "")) not in run_ids:
            continue
        if price_cents(node, "order_decided_price_cents") is None:
            continue
        if actual_price_cents(node) is None:
            continue
        if any(limit_cents(node, mode) is None for mode in _MODES):
            continue
        rows.append(node)
    return tuple(rows)


def _mode_report(mode: Mode, fills: tuple[Node, ...]) -> ModeReport:
    count = len(fills)
    filled = tuple(node for node in fills if _would_fill(node, mode))
    slippages = tuple(_slippage_bps(node) for node in filled)
    avg_slippage = None if not slippages else sum(slippages) / Decimal(len(slippages))
    drop_rate = Decimal("0") if count == 0 else Decimal(count - len(filled)) / count
    return ModeReport(
        mode=mode,
        order_count=count,
        would_have_filled=len(filled),
        drop_rate_pct=drop_rate * _PCT,
        avg_slippage_bps=avg_slippage,
    )


def _would_fill(node: Node, mode: Mode) -> bool:
    actual = actual_price_cents(node)
    limit = limit_cents(node, mode)
    if actual is None or limit is None:
        return False
    return actual <= limit if node.props.get("side") == "buy" else actual >= limit


def _slippage_bps(node: Node) -> Decimal:
    actual = Decimal(actual_price_cents(node) or 0)
    decided = Decimal(price_cents(node, "order_decided_price_cents") or 0)
    if decided <= 0:
        return Decimal("0")
    if node.props.get("side") == "sell":
        return (decided - actual) / decided * _BPS
    return (actual - decided) / decided * _BPS


def _fmt(value: Decimal) -> str:
    return str(value.quantize(_ONE_CENT, rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    raise SystemExit(main())
