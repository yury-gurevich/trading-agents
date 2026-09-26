"""Chain S&P 500 replay bars across source-symbol switches.

Agent: tooling
Role: rescale source windows so replay lines preserve raw switch-day returns.
External I/O: none; raw boundary closes are provided by the caller.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from scripts.sp500_bars import BarRow

RawClose = Callable[[str, date, date], float]


@dataclass(frozen=True)
class SwitchRecord:
    line: str
    from_symbol: str
    to_symbol: str
    from_date: date
    to_date: date
    raw_move: float
    move_vs_spy: float
    action: str


@dataclass(frozen=True)
class ChainResult:
    rows: tuple[BarRow, ...]
    switches: tuple[SwitchRecord, ...]


def chain_source_switches(
    rows: tuple[BarRow, ...] | list[BarRow],
    raw_close: RawClose,
    spy_closes: dict[date, float],
    action_lookup: Callable[[str, str, str, date, date], str] | None = None,
) -> ChainResult:
    """Return rows rescaled backwards at source switches using raw close ratios."""
    by_line: dict[str, list[BarRow]] = {}
    for row in rows:
        by_line.setdefault(row.line, []).append(row)
    chained: list[BarRow] = []
    switches: list[SwitchRecord] = []
    for _line, line_rows in by_line.items():
        result = _chain_line(sorted(line_rows, key=lambda item: item.date), raw_close)
        chained.extend(result)
        switches.extend(_switches(result, raw_close, spy_closes, action_lookup))
    return ChainResult(
        tuple(sorted(chained, key=lambda row: (row.line, row.date))),
        tuple(sorted(switches, key=lambda row: (row.line, row.to_date))),
    )


def _chain_line(rows: list[BarRow], raw_close: RawClose) -> list[BarRow]:
    segments = _segments(rows)
    if not segments:
        return []
    factors = [1.0 for _segment in segments]
    for index in range(len(segments) - 2, -1, -1):
        left = segments[index][-1]
        right = segments[index + 1][0]
        right_window_last = segments[index + 1][-1].date
        raw_ratio = raw_close(right.symbol, right.date, right_window_last) / raw_close(
            left.symbol, left.date, left.date
        )
        target_left_close = right.close * factors[index + 1] / raw_ratio
        factors[index] = target_left_close / left.close
    return [
        _scale(row, factors[index])
        for index, segment in enumerate(segments)
        for row in segment
    ]


def _segments(rows: list[BarRow]) -> list[list[BarRow]]:
    segments: list[list[BarRow]] = []
    for row in rows:
        if not segments or segments[-1][-1].symbol != row.symbol:
            segments.append([row])
        else:
            segments[-1].append(row)
    return segments


def _scale(row: BarRow, factor: float) -> BarRow:
    return BarRow(
        row.line,
        row.symbol,
        row.date,
        row.open * factor,
        row.high * factor,
        row.low * factor,
        row.close * factor,
    )


def _switches(
    rows: list[BarRow],
    raw_close: RawClose,
    spy_closes: dict[date, float],
    action_lookup: Callable[[str, str, str, date, date], str] | None,
) -> list[SwitchRecord]:
    out: list[SwitchRecord] = []
    segments = _segments(rows)
    for left_segment, right_segment in pairwise(segments):
        left = left_segment[-1]
        right = right_segment[0]
        right_window_last = right_segment[-1].date
        raw_ratio = raw_close(right.symbol, right.date, right_window_last) / raw_close(
            left.symbol, left.date, left.date
        )
        spy_ratio = spy_closes[right.date] / spy_closes[left.date]
        action = (
            action_lookup(left.line, left.symbol, right.symbol, left.date, right.date)
            if action_lookup is not None
            else ""
        )
        out.append(
            SwitchRecord(
                left.line,
                left.symbol,
                right.symbol,
                left.date,
                right.date,
                raw_ratio - 1.0,
                raw_ratio - spy_ratio,
                action,
            )
        )
    return out
