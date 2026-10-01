"""Synthetic caches for the S250 history-rule tests.

Agent: tooling
Role: write a one-year replay cache whose lines hold bars on chosen sessions only.
External I/O: local tmp files only.

Every price here is invented. The sessions are 2019's sessions by the provider's own
calendar, so the harness's declared window (203 sessions back from a session,
`PROV-TRG-05`) holds exactly 203 of them and a line's count inside it is plain
arithmetic. Passing 2019's real NYSE closures removes them, as the real cache does.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from scripts.replay_runner import run
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult

from agents.provider.domain.market_calendar import is_trading_session

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    import pytest

COUNTER = "member_sessions_below_required_history"
Seen = list[tuple[date, tuple[str, ...], frozenset[str]]]

# The declared window holds the analyst's 200 bars plus the provider's 3-session
# staleness buffer (`declared_lookback_days`, `max_staleness_days` = 3).
WINDOW_SESSIONS = 203


# NYSE's full-day closures of 2019. The provider's calendar lists 2024-2027 only and
# counts every weekday before 2024 as a session (`market_calendar.py`).
NYSE_CLOSURES_2019 = frozenset(
    date(2019, month, day)
    for month, day in (
        (1, 1),
        (1, 21),
        (2, 18),
        (4, 19),
        (5, 27),
        (7, 4),
        (9, 2),
        (11, 28),
        (12, 25),
    )
)


def sessions_2019(closures: frozenset[date] = frozenset()) -> tuple[date, ...]:
    """Every 2019 weekday (261: the calendar lists no 2019 closure), less `closures`."""
    day, out = date(2019, 1, 1), []
    while day.year == 2019:
        if is_trading_session(day) and day not in closures:
            out.append(day)
        day += timedelta(days=1)
    return tuple(out)


def bars_in_window(first_bar: int, index: int) -> int:
    """A line with every session from `first_bar`: its bars in `index`'s window."""
    return index - max(first_bar, index - WINDOW_SESSIONS + 1) + 1


def write_cache(
    cache: Path,
    lines: Mapping[str, Iterable[int]],
    closures: frozenset[date] = frozenset(),
) -> tuple[date, ...]:
    """A cache where each line is a member all year, with bars on the given indices."""
    cache.mkdir()
    sessions = sessions_2019(closures)
    episodes = tuple(Episode(line, line, sessions[0], sessions[-1]) for line in lines)
    membership = MembershipResult(
        episodes=episodes,
        members_by_session=dict.fromkeys(sessions, tuple(lines)),
        unreconciled=(),
        count_min=len(lines),
        count_max=len(lines),
    )
    bars = tuple(
        BarRow(line, line, sessions[index], 10.0, 10.2, 9.9, 10.0, 1_000_000)
        for line, indices in lines.items()
        for index in sorted(indices)
    )
    write_universe_cache(cache, sessions, membership, bars, {})
    _write_csv(
        cache / "sp500_benchmark.csv.gz",
        ["symbol", "date", "open", "high", "low", "close", "volume"],
        [["SPY", day.isoformat(), 300, 301, 299, 300, 100] for day in sessions],
    )
    _write_csv(
        cache / "sp500_vix.csv.gz",
        ["date", "vix_close"],
        [[day.isoformat(), 15] for day in sessions],
    )
    return sessions


def observe(
    monkeypatch: pytest.MonkeyPatch, approve: Mapping[date, Any] | None = None
) -> Seen:
    """Fake the day runner: record each session's tickers and bar tickers."""
    seen: Seen = []

    def fake_day(inputs: Any, settings: object) -> object:
        del settings
        tickers = frozenset(bar.ticker for bar in inputs.bars)
        seen.append((inputs.session, inputs.tickers, tickers))
        orders = (approve or {}).get(inputs.session, ())
        return SimpleNamespace(absent_inputs={}, approved=orders)

    monkeypatch.setattr("scripts.replay_runner.run_replay_day", fake_day)
    return seen


def run_window(
    cache: Path,
    out: Path,
    sessions: tuple[date, ...],
    *,
    start: int,
    end: int,
    **kwargs: Any,
) -> dict[str, Any]:
    """Replay sessions `start` to `end` (indices) through the real runner."""
    return run(
        cache_dir=cache,
        out=out,
        start=sessions[start],
        end=sessions[end],
        overrides=kwargs.pop("overrides", ()),
        progress_every=0,
        **kwargs,
    )


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
