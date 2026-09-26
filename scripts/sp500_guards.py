"""Build guards for suspicious S&P 500 replay price moves.

Agent: tooling
Role: fail replay builds when source switches or single-day moves lack evidence.
External I/O: reads the committed known-moves CSV.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.sp500_bars import BarRow
    from scripts.sp500_chain import SwitchRecord

SWITCH_MOVE_LIMIT = 0.10  # Row 12: largest ordinary measured switch was +6.4%.
MOVE_REVIEW_LIMIT = 0.50  # Row 13: 10 measured same-source moves need review.
KNOWN_MOVES_PATH = Path(__file__).with_name("sp500_known_moves.csv")
KNOWN_MOVE_KINDS = frozenset({"event", "distribution", "adjustment-error"})


@dataclass(frozen=True)
class KnownMove:
    line: str
    date: date
    kind: str
    evidence: str


@dataclass(frozen=True)
class MoveReview:
    line: str
    symbol: str
    date: date
    move_vs_spy: float
    kind: str
    evidence: str


def load_known_moves(path: Path = KNOWN_MOVES_PATH) -> tuple[KnownMove, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            kind = row["kind"]
            if kind not in KNOWN_MOVE_KINDS:
                raise ValueError(f"unknown known-move kind {kind!r}")
            rows.append(
                KnownMove(
                    row["line"],
                    date.fromisoformat(row["date"]),
                    kind,
                    row["evidence"],
                )
            )
    return tuple(rows)


def require_switch_actions(switches: tuple[SwitchRecord, ...]) -> None:
    missing = [
        switch
        for switch in switches
        if abs(switch.move_vs_spy) > SWITCH_MOVE_LIMIT and not switch.action
    ]
    if missing:
        details = ", ".join(
            f"{row.line} {row.from_symbol}->{row.to_symbol} {row.to_date}"
            for row in missing
        )
        raise SystemExit(f"switch move lacks action: {details}")


def review_same_source_moves(
    rows: tuple[BarRow, ...],
    spy_closes: dict[date, float],
    known_moves: tuple[KnownMove, ...],
) -> tuple[MoveReview, ...]:
    known = {(row.line, row.date): row for row in known_moves}
    reviews: list[MoveReview] = []
    missing: list[str] = []
    for left, right in pairwise(rows):
        if left.line != right.line or left.symbol != right.symbol:
            continue
        stock_ratio = right.close / left.close
        spy_ratio = spy_closes[right.date] / spy_closes[left.date]
        move_vs_spy = stock_ratio - spy_ratio
        if abs(move_vs_spy) <= MOVE_REVIEW_LIMIT:
            continue
        known_move = known.get((right.line, right.date))
        if known_move is None:
            missing.append(f"{right.line} {right.symbol} {right.date}")
            continue
        reviews.append(
            MoveReview(
                right.line,
                right.symbol,
                right.date,
                move_vs_spy,
                known_move.kind,
                known_move.evidence,
            )
        )
    if missing:
        detail = ", ".join(missing)
        raise SystemExit(f"same-source move lacks known-move entry: {detail}")
    return tuple(reviews)


def known_move_counts(moves: tuple[KnownMove, ...]) -> dict[str, int]:
    return dict(sorted(Counter(move.kind for move in moves).items()))
