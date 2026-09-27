"""Mark and rebase S235 replay positions over cached bar series.

Agent: tooling
Role: carry forward gap marks, force ended-line exits, and handle adjustment days.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from scripts.replay_broker import ReplayPosition, apply_adjustment_rebase

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date
    from typing import Any

    from scripts.sp500_bars import BarRow
    from scripts.sp500_guards import KnownMove
    from scripts.sp500_membership import Episode


class MarkResult(NamedTuple):
    equity_cents: int
    long_cents: int
    gap_marks: int


class ExitResult(NamedTuple):
    cash_delta_cents: int
    data_end_exits: int
    membership_end_exits: int


@dataclass(frozen=True)
class AdjustmentResult:
    count: int
    lines: frozenset[str]


def mark_positions(
    cash_cents: int,
    positions: dict[str, ReplayPosition],
    line_bars: Mapping[str, tuple[BarRow, ...]],
    session: date,
) -> MarkResult:
    """Mark held positions at today's close or a carried last close."""
    long_cents = 0
    gap_marks = 0
    for line, position in positions.items():
        latest = _latest_on_or_before(line_bars.get(line, ()), session)
        if latest is None:
            continue
        long_cents += _position_value_cents(position, _close_cents(latest))
        if latest.date != session and _has_future_bar(line_bars.get(line, ()), session):
            gap_marks += 1
    return MarkResult(cash_cents + long_cents, long_cents, gap_marks)


def exit_ended_positions(
    session: date,
    positions: dict[str, ReplayPosition],
    line_bars: Mapping[str, tuple[BarRow, ...]],
    episodes: tuple[Episode, ...],
    fills: list[dict[str, Any]],
) -> ExitResult:
    """Sell held lines at the last close once their bar series has ended."""
    cash_delta = data_end = membership_end = 0
    for line, position in tuple(positions.items()):
        rows = line_bars.get(line, ())
        if not rows or rows[-1].date > session:
            continue
        last = rows[-1]
        price_cents = _position_price_cents(position, _close_cents(last))
        reason = _end_reason(line, last.date, episodes)
        fills.append(
            {
                "date": last.date.isoformat(),
                "line": line,
                "side": "sell",
                "quantity": position.quantity,
                "price_cents": price_cents,
                "reason": reason,
            }
        )
        cash_delta += position.quantity * price_cents
        data_end += int(reason == "data_end")
        membership_end += int(reason == "membership_end")
        positions.pop(line, None)
    return ExitResult(cash_delta, data_end, membership_end)


def apply_adjustment_rebases(
    session: date,
    positions: dict[str, ReplayPosition],
    line_bars: Mapping[str, tuple[BarRow, ...]],
    known_moves: tuple[KnownMove, ...],
) -> AdjustmentResult:
    """Rebase held lines on listed adjustment-error dates."""
    rebased: set[str] = set()
    known = {
        row.line
        for row in known_moves
        if row.date == session and row.kind == "adjustment-error"
    }
    for line in sorted(known & positions.keys()):
        ratio = _same_line_ratio(line_bars.get(line, ()), session)
        if ratio is None:
            continue
        positions[line] = apply_adjustment_rebase(positions[line], ratio=ratio)
        rebased.add(line)
    return AdjustmentResult(count=len(rebased), lines=frozenset(rebased))


def _latest_on_or_before(rows: tuple[BarRow, ...], session: date) -> BarRow | None:
    latest = None
    for row in rows:
        if row.date > session:
            break
        latest = row
    return latest


def _has_future_bar(rows: tuple[BarRow, ...], session: date) -> bool:
    return any(row.date > session for row in rows)


def _same_line_ratio(rows: tuple[BarRow, ...], session: date) -> float | None:
    prior = None
    for row in rows:
        if row.date == session and prior is not None and prior.close:
            return row.close / prior.close
        if row.date >= session:
            return None
        prior = row
    return None


def _end_reason(line: str, last_bar: date, episodes: tuple[Episode, ...]) -> str:
    return (
        "data_end"
        if any(row.line == line and row.last == last_bar for row in episodes)
        else "membership_end"
    )


def _close_cents(row: BarRow) -> int:
    return round(row.close * 100)


def _position_value_cents(position: ReplayPosition, close_cents: int) -> int:
    return position.quantity * _position_price_cents(position, close_cents)


def _position_price_cents(position: ReplayPosition, price_cents: int) -> int:
    return round(price_cents * position.price_scale)
