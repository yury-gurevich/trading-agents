"""Mark and rebase S235 replay positions over cached bar series.

Agent: tooling
Role: carry forward gap marks, force ended-line exits, and handle adjustment days.
External I/O: none.
"""

from __future__ import annotations

from bisect import bisect_left
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
    """Sell a held line at today's close when its episode has no later bar.

    Decided per membership episode, never per line: a line that leaves the index and
    returns years later is sold when its episode ends, not carried at a frozen price.
    `membership_end`: the episode ends today. `data_end`: bars stop before it does (a
    deal closes before the removal date). A member at the cache's end is not sold
    (DL-234 amendment).
    """
    cash_delta = data_end = membership_end = 0
    cache_end = max((row.last for row in episodes), default=session)
    spans = _episodes_by_line(episodes)
    for line, position in tuple(positions.items()):
        rows = line_bars.get(line, ())
        reason = _ended_today(rows, session, spans.get(line, ()), cache_end)
        if reason is None:
            continue
        today = rows[_index_of(rows, session) or 0]
        price_cents = _position_price_cents(position, _close_cents(today))
        fills.append(
            {
                "date": session.isoformat(),
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


def _ended_today(
    rows: tuple[BarRow, ...],
    session: date,
    spans: tuple[Episode, ...],
    cache_end: date,
) -> str | None:
    """The exit reason when today is the line's last bar in its episode, else None."""
    index = _index_of(rows, session)
    if index is None:
        return None
    episode = next((row for row in spans if row.first <= session <= row.last), None)
    if episode is None:
        return "membership_end"
    if episode.last >= cache_end:
        return None  # still a member when the cache ends: bars stop with the cache
    following = rows[index + 1].date if index + 1 < len(rows) else None
    if following is not None and following <= episode.last:
        return None
    return "membership_end" if session == episode.last else "data_end"


def _episodes_by_line(episodes: tuple[Episode, ...]) -> dict[str, tuple[Episode, ...]]:
    spans: dict[str, list[Episode]] = {}
    for row in episodes:
        spans.setdefault(row.line, []).append(row)
    return {line: tuple(rows) for line, rows in spans.items()}


def _index_of(rows: tuple[BarRow, ...], session: date) -> int | None:
    dates = [row.date for row in rows]
    index = bisect_left(dates, session)
    return index if index < len(rows) and rows[index].date == session else None


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


def _close_cents(row: BarRow) -> int:
    return round(row.close * 100)


def _position_value_cents(position: ReplayPosition, close_cents: int) -> int:
    return position.quantity * _position_price_cents(position, close_cents)


def _position_price_cents(position: ReplayPosition, price_cents: int) -> int:
    return round(price_cents * position.price_scale)
