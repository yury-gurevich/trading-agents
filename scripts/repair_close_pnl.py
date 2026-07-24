"""Invalidate decision-time CloseDecision PnL without rewriting history.

Agent: tooling
Role: append ADR-0015 realized-PnL correction markers to affected close decisions.
External I/O: PostgreSQL database when run as a CLI.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from kernel import GraphStore, Node, PostgresGraphSettings, PostgresGraphStore

REASON = "decision-time PnL with no fill (ADR-0015 §1)"
_FILLED_STATUSES = frozenset({"filled", "partial", "partially_filled"})


@dataclass(frozen=True)
class RepairRow:
    """One CloseDecision repair verdict."""

    ticker: str
    trigger: str
    pnl_cents: int
    verdict: str


@dataclass(frozen=True)
class RepairReport:
    """Aggregate repair results."""

    rows: tuple[RepairRow, ...]
    invalidated: int
    manual_review: int
    skipped_invalidated: int


def repair_graph(
    graph: GraphStore, *, apply: bool = False, now: datetime | None = None
) -> RepairReport:
    """Inspect CloseDecision nodes and optionally append invalidation markers."""
    stamp = (now or datetime.now(tz=UTC)).astimezone(UTC).isoformat()
    rows: list[RepairRow] = []
    invalidated = 0
    manual_review = 0
    skipped_invalidated = 0
    for close in graph.list_nodes("CloseDecision"):
        pnl = close.props.get("pnl_cents")
        if not isinstance(pnl, int) or isinstance(pnl, bool):
            continue
        if "pnl_invalidated_at" in close.props:
            skipped_invalidated += 1
            continue
        if _filled_sell_exists(graph, close):
            manual_review += 1
            verdict = "manual_review_filled_sell"
        else:
            invalidated += 1
            verdict = "would_invalidate" if not apply else "invalidated"
            if apply:
                graph.merge_node(
                    "CloseDecision",
                    close.key,
                    {
                        "pnl_invalidated_at": stamp,
                        "pnl_invalidated_reason": REASON,
                    },
                )
        rows.append(
            RepairRow(
                ticker=str(close.props.get("ticker", "")),
                trigger=str(close.props.get("trigger", "")),
                pnl_cents=pnl,
                verdict=verdict,
            )
        )
    return RepairReport(
        rows=tuple(rows),
        invalidated=invalidated,
        manual_review=manual_review,
        skipped_invalidated=skipped_invalidated,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the dry-run/default or apply repair against the configured graph."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write repair markers")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="explicit .env path containing POSTGRES_DSN",
    )
    args = parser.parse_args(argv)
    load_dotenv(Path(args.env_file), override=False)
    dsn = os.environ.get("POSTGRES_DSN", "")
    if not dsn:
        parser.error("POSTGRES_DSN is required")

    graph = PostgresGraphStore(PostgresGraphSettings(postgres_dsn=dsn))
    try:
        report = repair_graph(graph, apply=args.apply)
    finally:
        graph.close()
    _print_report(report, apply=args.apply)
    return 0


def _filled_sell_exists(graph: GraphStore, close: Node) -> bool:
    position = _position_for_close(graph, close)
    if position is not None:
        for fill in graph.ancestors(position, max_depth=1, edge_types={"CLOSES"}):
            if _is_filled_sell(fill, close, position.key):
                return True
    position_id = str(close.props.get("position_id", ""))
    if not position_id:
        return False
    return any(
        _is_filled_sell(fill, close, position_id)
        for fill in graph.list_nodes("Fill")
        if _fill_matches_position(fill, position_id)
    )


def _position_for_close(graph: GraphStore, close: Node) -> Node | None:
    position_id = close.props.get("position_id")
    if isinstance(position_id, str):
        found = graph.get_node("Position", position_id)
        if found is not None:
            return found
    return next(
        iter(graph.descendants(close, max_depth=1, edge_types={"CLOSES"})), None
    )


def _is_filled_sell(fill: Node, close: Node, position_id: str) -> bool:
    return (
        fill.label == "Fill"
        and fill.props.get("side") == "sell"
        and fill.props.get("ticker") == close.props.get("ticker")
        and _filled_status(fill)
        and _fill_matches_position(fill, position_id)
    )


def _filled_status(fill: Node) -> bool:
    values = (fill.props.get("status"), fill.props.get("broker_status"))
    return any(str(value).lower() in _FILLED_STATUSES for value in values)


def _fill_matches_position(fill: Node, position_id: str) -> bool:
    return (
        fill.props.get("position_id") == position_id
        or fill.key.endswith(f":sell:{position_id}")
        or f":{position_id}:" in fill.key
    )


def _print_report(report: RepairReport, *, apply: bool) -> None:
    print(f"mode={'apply' if apply else 'dry-run'}")
    print("ticker\ttrigger\tpnl_cents\tverdict")
    for row in report.rows:
        print(f"{row.ticker}\t{row.trigger}\t{row.pnl_cents}\t{row.verdict}")
    print(
        "totals "
        f"candidates={len(report.rows)} "
        f"invalidated={report.invalidated} "
        f"manual_review={report.manual_review} "
        f"skipped_invalidated={report.skipped_invalidated}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
