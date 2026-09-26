"""Helpers for building the S&P 500 replay cache from fetched windows.

Agent: tooling
Role: adapt bar fetchers and symbol-map actions for replay cache construction.
External I/O: Alpaca market data through an injected or real bar fetcher.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any, Protocol

BarFetcher = Callable[..., dict[str, list[Any]]]


class SymbolMapLike(Protocol):
    kind: str
    line: str
    symbol: str
    from_date: date
    to_date: date | None
    action: str


def raw_close_fetcher(bar_fetcher: BarFetcher) -> Callable[[str, date, date], float]:
    def raw_close(symbol: str, day: date, asof: date) -> float:
        rows = bar_fetcher(
            [symbol],
            end=day.isoformat(),
            start=day.isoformat(),
            asof=asof.isoformat(),
            adjustment="raw",
        ).get(symbol, ())
        for row in rows:
            if date.fromisoformat(str(row[0])[:10]) == day:
                return float(row[4])
        raise RuntimeError(f"missing raw boundary close for {symbol} {day}")

    return raw_close


def action_lookup(
    map_rows: tuple[SymbolMapLike, ...],
) -> Callable[[str, str, str, date, date], str]:
    def lookup(
        line: str, from_symbol: str, to_symbol: str, from_date: date, to_date: date
    ) -> str:
        matches = [
            row.action
            for row in map_rows
            if row.line == line
            and _row_owns_switch(row, from_symbol, to_symbol, from_date, to_date)
            and row.action
        ]
        if len(set(matches)) > 1:
            message = f"multiple actions claim switch {line} {from_symbol}->{to_symbol}"
            raise RuntimeError(message)
        return matches[0] if matches else ""

    return lookup


def _row_owns_switch(
    row: SymbolMapLike, from_symbol: str, to_symbol: str, from_date: date, to_date: date
) -> bool:
    if row.kind == "bars" and row.symbol == from_symbol and row.to_date == from_date:
        return True
    if row.kind == "bars" and row.symbol == to_symbol and row.from_date == to_date:
        return True
    return (
        row.kind == "rename" and row.symbol == from_symbol and row.from_date == to_date
    )
