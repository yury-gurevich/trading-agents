"""Measure S&P 500 replay-universe bar coverage over market sessions.

Agent: tooling
Role: classify member-session coverage and fail builds below the named floor.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from scripts.sp500_bars import BarRow
    from scripts.sp500_membership import Episode

# E17.1 accepted roughly 90% member-session coverage as enough to proceed.
COVERAGE_FLOOR = 0.90


@dataclass(frozen=True)
class Shortfall:
    line: str
    first: date
    last: date
    reason: str
    missing_sessions: int


@dataclass(frozen=True)
class CoverageReport:
    member_sessions: int
    covered_sessions: int
    ratio: float
    shortfalls: tuple[Shortfall, ...]


def coverage_report(
    episodes: list[Episode] | tuple[Episode, ...],
    bars: list[BarRow] | tuple[BarRow, ...],
    sessions: list[date] | tuple[date, ...],
) -> CoverageReport:
    sessions_by_line = _episode_sessions(episodes, sessions)
    bars_by_line: dict[str, set[date]] = {}
    for row in bars:
        bars_by_line.setdefault(row.line, set()).add(row.date)
    member_sessions = sum(len(days) for days in sessions_by_line.values())
    covered = 0
    shortfalls: list[Shortfall] = []
    for line, days in sessions_by_line.items():
        actual = bars_by_line.get(line, set()) & set(days)
        covered += len(actual)
        shortfalls.extend(_shortfalls(line, days, actual))
    ratio = covered / member_sessions if member_sessions else 1.0
    return CoverageReport(member_sessions, covered, ratio, tuple(shortfalls))


def require_floor(report: CoverageReport) -> None:
    if report.ratio < COVERAGE_FLOOR:
        message = f"coverage {report.ratio:.2%} below floor {COVERAGE_FLOOR:.0%}"
        raise SystemExit(message)


def _episode_sessions(
    episodes: list[Episode] | tuple[Episode, ...],
    sessions: list[date] | tuple[date, ...],
) -> dict[str, list[date]]:
    out: dict[str, list[date]] = {}
    for episode in episodes:
        out.setdefault(episode.line, []).extend(
            session for session in sessions if episode.first <= session <= episode.last
        )
    return {line: sorted(set(days)) for line, days in out.items()}


def _shortfalls(
    line: str, days: list[date], actual: set[date]
) -> tuple[Shortfall, ...]:
    if not days:
        return ()
    if not actual:
        return (Shortfall(line, days[0], days[-1], "no bars", len(days)),)
    out: list[Shortfall] = []
    actual_days = sorted(actual)
    if actual_days[0] > days[0]:
        missing = [day for day in days if day < actual_days[0]]
        out.append(
            Shortfall(line, missing[0], missing[-1], "starts late", len(missing))
        )
    if actual_days[-1] < days[-1]:
        missing = [day for day in days if day > actual_days[-1]]
        out.append(Shortfall(line, missing[0], missing[-1], "ends early", len(missing)))
    interior = [
        day
        for day in days
        if actual_days[0] < day < actual_days[-1] and day not in actual
    ]
    if interior:
        out.append(Shortfall(line, interior[0], interior[-1], "gap", len(interior)))
    return tuple(out)
