"""Reconstruct point-in-time S&P 500 membership from Wikipedia rows.

Agent: tooling
Role: convert current constituents, dated changes, and a symbol map into episodes.
External I/O: reads the committed symbol-map CSV when requested.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.sp500_wiki import Change, Constituent

MAP_PATH = Path(__file__).with_name("sp500_symbol_map.csv")


@dataclass(frozen=True)
class SymbolMapRow:
    kind: str
    line: str
    symbol: str
    from_date: date
    to_date: date | None
    evidence: str


@dataclass(frozen=True)
class Episode:
    line: str
    ticker: str
    first: date
    last: date


@dataclass(frozen=True)
class UnreconciledRecord:
    date: date
    ticker: str
    reason: str


@dataclass(frozen=True)
class MembershipResult:
    episodes: tuple[Episode, ...]
    members_by_session: dict[date, tuple[str, ...]]
    count_min: int
    count_max: int
    unreconciled: tuple[UnreconciledRecord, ...]


def load_symbol_map(path: Path = MAP_PATH) -> tuple[SymbolMapRow, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(
            SymbolMapRow(
                kind=row["kind"],
                line=row["line"],
                symbol=row["symbol"],
                from_date=date.fromisoformat(row["from"]),
                to_date=date.fromisoformat(row["to"]) if row["to"] else None,
                evidence=row["evidence"],
            )
            for row in csv.DictReader(handle)
        )


def reconstruct_membership(
    constituents: list[Constituent] | tuple[Constituent, ...],
    changes: list[Change] | tuple[Change, ...],
    sessions: list[date] | tuple[date, ...],
    symbol_map: list[SymbolMapRow] | tuple[SymbolMapRow, ...] | None = None,
) -> MembershipResult:
    """Undo changes to the first session, then replay them forward."""
    ordered_sessions = tuple(sorted(sessions))
    if not ordered_sessions:
        raise ValueError("sessions must not be empty")
    rows = tuple(symbol_map) if symbol_map is not None else load_symbol_map()
    rename_rows = tuple(row for row in rows if row.kind == "rename")
    ordered_changes = tuple(sorted(changes, key=lambda change: change.date))
    active = {
        _line_for(row.symbol, ordered_sessions[-1], rename_rows) for row in constituents
    }
    unreconciled: list[UnreconciledRecord] = []
    first_session = ordered_sessions[0]
    for change in reversed(ordered_changes):
        if change.date <= first_session:
            continue
        _undo_change(active, change, rename_rows, unreconciled)
    members: dict[date, tuple[str, ...]] = {}
    replay = iter(change for change in ordered_changes if change.date > first_session)
    next_change = next(replay, None)
    for session in ordered_sessions:
        while next_change is not None and next_change.date <= session:
            _apply_change(active, next_change, rename_rows)
            next_change = next(replay, None)
        members[session] = tuple(
            sorted(_ticker_for(line, session, rename_rows) for line in active)
        )
    counts = [len(names) for names in members.values()]
    return MembershipResult(
        episodes=_episodes(members, rename_rows),
        members_by_session=members,
        count_min=min(counts),
        count_max=max(counts),
        unreconciled=tuple(unreconciled),
    )


def _undo_change(
    active: set[str],
    change: Change,
    renames: tuple[SymbolMapRow, ...],
    unreconciled: list[UnreconciledRecord],
) -> None:
    if change.added is not None:
        line = _line_for(change.added, change.date, renames)
        if line in active:
            active.remove(line)
        else:
            unreconciled.append(
                UnreconciledRecord(change.date, change.added, "added ticker absent")
            )
    if change.removed is not None:
        active.add(_line_for(change.removed, change.date, renames))


def _apply_change(
    active: set[str], change: Change, renames: tuple[SymbolMapRow, ...]
) -> None:
    if change.removed is not None:
        active.discard(_line_for(change.removed, change.date, renames))
    if change.added is not None:
        active.add(_line_for(change.added, change.date, renames))


def _line_for(symbol: str, when: date, renames: tuple[SymbolMapRow, ...]) -> str:
    for row in renames:
        if symbol == row.symbol and when < row.from_date:
            return row.line
    return symbol


def _ticker_for(line: str, when: date, renames: tuple[SymbolMapRow, ...]) -> str:
    for row in sorted(renames, key=lambda item: item.from_date):
        if line == row.line and when < row.from_date:
            return row.symbol
    return line


def _episodes(
    members: dict[date, tuple[str, ...]], renames: tuple[SymbolMapRow, ...]
) -> tuple[Episode, ...]:
    active: dict[tuple[str, str], date] = {}
    episodes: list[Episode] = []
    previous: date | None = None
    for session, tickers in sorted(members.items()):
        seen = {(_line_for(ticker, session, renames), ticker) for ticker in tickers}
        for key, start in tuple(active.items()):
            if key not in seen:
                if previous is None:
                    continue
                episodes.append(Episode(key[0], key[1], start, previous))
                del active[key]
        for key in seen:
            active.setdefault(key, session)
        previous = session
    if previous is None:
        return ()
    episodes.extend(
        Episode(line, ticker, start, previous)
        for (line, ticker), start in active.items()
    )
    return tuple(
        sorted(episodes, key=lambda item: (item.first, item.line, item.ticker))
    )
