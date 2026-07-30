"""Compare flat vs volatility-scaled stop/target proposal evidence.

Agent: tooling
Role: report ADR-0013 challenger evidence from persisted Recommendation records.
External I/O: graph reads when run as a CLI.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from statistics import median
from typing import TYPE_CHECKING, Literal

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if TYPE_CHECKING:
    from kernel import GraphStore, Node

Mode = Literal["flat", "scaled"]

_ONE_HUNDRED = Decimal("100")
_ONE_CENT = Decimal("0.01")
_MODES: tuple[Mode, ...] = ("flat", "scaled")
_OUTCOME_DRAWDOWN_PROP = "stop_target_observed_drawdown_pct"


@dataclass(frozen=True)
class ModeReport:
    mode: Mode
    recommendations: int
    stop_min_pct: Decimal | None
    stop_median_pct: Decimal | None
    stop_max_pct: Decimal | None
    rr_pass_rate_pct: Decimal
    known_outcomes: int
    would_touch_rate_pct: Decimal | None


def compare_stop_targets(
    graph: GraphStore,
    *,
    run_ids: tuple[str, ...] = (),
    min_reward_risk_ratio: Decimal = Decimal("1.5"),
) -> tuple[ModeReport, ...]:
    """Return report rows for recommendations with S150 stop-target evidence."""
    nodes = tuple(_eligible_recommendations(graph, frozenset(run_ids)))
    return tuple(_mode_report(mode, nodes, min_reward_risk_ratio) for mode in _MODES)


def render_report(rows: tuple[ModeReport, ...]) -> str:
    lines = [
        "mode\trecommendations\tstop_min_pct\tstop_median_pct\tstop_max_pct\t"
        "rr_pass_rate_pct\tknown_outcomes\twould_touch_rate_pct"
    ]
    lines.extend(
        "\t".join(
            (
                row.mode,
                str(row.recommendations),
                _fmt_optional(row.stop_min_pct),
                _fmt_optional(row.stop_median_pct),
                _fmt_optional(row.stop_max_pct),
                _fmt(row.rr_pass_rate_pct),
                str(row.known_outcomes),
                _fmt_optional(row.would_touch_rate_pct),
            )
        )
        for row in rows
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env", help="path to .env")
    parser.add_argument(
        "--run-id",
        action="append",
        default=[],
        help="Analyst run id to include; repeat for a run window",
    )
    parser.add_argument("--min-rr", default="1.5", help="reward/risk pass threshold")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv

    from kernel.graph_env import build_graph_from_env

    load_dotenv(Path(args.env_file), override=False)
    graph = build_graph_from_env()
    try:
        rows = compare_stop_targets(
            graph,
            run_ids=tuple(args.run_id),
            min_reward_risk_ratio=Decimal(str(args.min_rr)),
        )
        print(render_report(rows))
    finally:
        close = getattr(graph, "close", None)
        if close is not None:
            close()
    return 0


def _eligible_recommendations(
    graph: GraphStore, run_ids: frozenset[str]
) -> tuple[Node, ...]:
    rows: list[Node] = []
    for node in graph.list_nodes("Recommendation"):
        if run_ids and _run_id(node) not in run_ids:
            continue
        has_stops = all(
            _pct(node, f"stop_target_{mode}_stop_pct") is not None for mode in _MODES
        )
        if has_stops:
            rows.append(node)
    return tuple(rows)


def _mode_report(
    mode: Mode, nodes: tuple[Node, ...], min_reward_risk_ratio: Decimal
) -> ModeReport:
    stops = tuple(_pct(node, f"stop_target_{mode}_stop_pct") for node in nodes)
    targets = tuple(_pct(node, f"stop_target_{mode}_target_pct") for node in nodes)
    stop_values = tuple(value for value in stops if value is not None)
    passed = sum(
        1
        for stop, target in zip(stops, targets, strict=True)
        if _rr_passes(stop, target, min_reward_risk_ratio)
    )
    known: list[tuple[Decimal, Decimal]] = []
    for stop, node in zip(stops, nodes, strict=True):
        drawdown = _pct(node, _OUTCOME_DRAWDOWN_PROP)
        if stop is not None and drawdown is not None:
            known.append((stop, drawdown))
    touched = 0
    for stop, drawdown in known:
        if drawdown >= stop:
            touched += 1
    median_stop = (
        Decimal(str(median(stop_values))) * _ONE_HUNDRED if stop_values else None
    )
    return ModeReport(
        mode=mode,
        recommendations=len(nodes),
        stop_min_pct=min(stop_values) * _ONE_HUNDRED if stop_values else None,
        stop_median_pct=median_stop,
        stop_max_pct=max(stop_values) * _ONE_HUNDRED if stop_values else None,
        rr_pass_rate_pct=_rate(passed, len(nodes)),
        known_outcomes=len(known),
        would_touch_rate_pct=None if not known else _rate(touched, len(known)),
    )


def _rr_passes(
    stop: Decimal | None, target: Decimal | None, min_reward_risk_ratio: Decimal
) -> bool:
    return (
        stop is not None
        and target is not None
        and stop > 0
        and target / stop >= min_reward_risk_ratio
    )


def _run_id(node: Node) -> str:
    return node.key.split(":", 1)[0]


def _pct(node: Node, field: str) -> Decimal | None:
    value = node.props.get(field)
    if not isinstance(value, int | float | Decimal):
        return None
    return Decimal(str(value))


def _rate(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return Decimal(numerator) / Decimal(denominator) * _ONE_HUNDRED


def _fmt_optional(value: Decimal | None) -> str:
    return "n/a" if value is None else _fmt(value)


def _fmt(value: Decimal) -> str:
    return str(value.quantize(_ONE_CENT, rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    raise SystemExit(main())
