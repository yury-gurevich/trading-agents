"""Build EXP-015's panel from the S235 cache as the replay offers it (S289).

Agent: tooling
Role: offer each session's members as the replay does (the declared lookback and
      the history rule), keep the scanner's survivors (primary) and the lines with 253
      bars (secondary), score each by the analyst's code, attach features and returns.
External I/O: progress lines on stderr; the cache is read by the caller.
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scripts.exp015_features import line_features
from scripts.exp015_spec import HORIZONS, LINE_FEATURES, MIN_SECONDARY_BARS
from scripts.exp015_store import Panel
from scripts.exp015_targets import adjustment_masks, forward_returns
from scripts.replay_history import offer_lines, visible_window
from scripts.replay_series import benchmark_window, contract_bars, members_on

from agents.analyst.domain.scoring import score_candidate
from agents.scanner.domain.filters import apply_filters
from contracts.scanner import Candidate

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from datetime import date

    from scripts.replay_cache import ReplayContext
    from scripts.replay_settings import ReplaySettings
    from scripts.sp500_bars import BarRow

    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class _Line:
    features: np.ndarray  # bars x LINE_FEATURES
    returns: np.ndarray  # bars x HORIZONS
    position: dict[date, int]


def build_panel(
    context: ReplayContext,
    settings: ReplaySettings,
    line_bars: dict[str, tuple[BarRow, ...]],
    adjustment_errors: dict[str, tuple[date, ...]],
    sessions: Sequence[date],
    lines: Collection[str] | None = None,
) -> tuple[Panel, dict[str, int]]:
    """The panel over `sessions`, members limited to `lines` when given; its counts."""
    every = context.universe.sessions
    index = {day: j for j, day in enumerate(every)}
    spy = _spy_forward(context, every, index)
    prepared = {
        line: _prepare(rows, context, adjustment_errors.get(line, ()), index, every)
        for line, rows in line_bars.items()
        if lines is None or line in lines
    }
    rows: list[tuple[object, ...]] = []
    counts: Counter[str] = Counter()
    for n, session in enumerate(sessions):
        members = tuple(
            m for m in members_on(context.universe, session) if m in prepared
        )
        window = visible_window(settings, line_bars, members, session)
        offered = offer_lines(settings, members, window, ())
        contract = contract_bars(offered.bars)
        bench = benchmark_window(context.benchmark, session, offered.bars)
        survivors, _ = apply_filters(
            offered.members,
            contract,
            bench,
            {},
            session,
            settings.scanner,
            earnings_horizon_days=None,
        )
        primary = {survivor.ticker for survivor in survivors}
        by_line: dict[str, list[OHLCVBar]] = {}
        for bar in contract:
            by_line.setdefault(bar.ticker, []).append(bar)
        counts["members_not_offered"] += len(members) - len(offered.members)
        for line in offered.members:
            prep = prepared[line]
            pos = prep.position.get(session)
            if pos is None:
                continue
            secondary = pos + 1 >= MIN_SECONDARY_BARS
            if line not in primary and not secondary:
                continue
            candidate = Candidate(ticker=line, rank=1, score=0.0, survived_filters=())
            score = score_candidate(
                candidate, tuple(by_line[line]), {}, bench, (), settings.analyst
            ).technical_score
            sector = context.sectors.get(line) or ""
            counts["rows_without_sector"] += not sector
            flags = (line in primary, secondary, score)
            arrays = (prep.features[pos], prep.returns[pos], spy[session])
            rows.append((session.isoformat(), line, sector, *flags, *arrays))
        if (n + 1) % 100 == 0 or n + 1 == len(sessions):
            line_out = (
                f"exp015 panel {session} {n + 1}/{len(sessions)} rows={len(rows)}"
            )
            print(line_out, file=sys.stderr, flush=True)
    return _panel(rows), dict(sorted(counts.items()))


def _prepare(
    rows: tuple[BarRow, ...],
    context: ReplayContext,
    moves: tuple[date, ...],
    index: dict[date, int],
    every: tuple[date, ...],
) -> _Line:
    dates = [row.date for row in rows]
    column = {
        name: np.array([getattr(row, name) for row in rows], dtype=float)
        for name in ("open", "high", "low", "close", "volume")
    }
    spy_closes = np.array([context.spy_closes.get(day, np.nan) for day in dates])
    named = line_features(
        column["high"], column["low"], column["close"], column["volume"], spy_closes
    )
    features = np.column_stack([named[name] for name in LINE_FEATURES])
    returns = forward_returns(dates, column["open"], column["close"], index, every)
    feature_mask, target_mask = adjustment_masks(dates, moves, index)
    features[feature_mask] = np.nan
    returns[target_mask] = np.nan
    return _Line(features, returns, {day: i for i, day in enumerate(dates)})


def _spy_forward(
    context: ReplayContext, every: tuple[date, ...], index: dict[date, int]
) -> dict[date, np.ndarray]:
    days = [day for day in every if day in context.benchmark]
    opens = np.array([context.benchmark[day].open for day in days])
    closes = np.array([context.benchmark[day].close for day in days])
    returns = forward_returns(days, opens, closes, index, every)
    out = {day: np.full(len(HORIZONS), np.nan) for day in every}
    out.update({day: returns[i] for i, day in enumerate(days)})
    return out


def _panel(rows: list[tuple[object, ...]]) -> Panel:
    columns = list(zip(*rows, strict=True)) if rows else [()] * 9
    return Panel(
        np.array(columns[0], dtype=str),
        np.array(columns[1], dtype=str),
        np.array(columns[2], dtype=str),
        np.array(columns[3], dtype=bool),
        np.array(columns[4], dtype=bool),
        np.array(columns[5], dtype=float),
        np.array(columns[6], dtype=float).reshape(-1, len(LINE_FEATURES)),
        np.array(columns[7], dtype=float).reshape(-1, len(HORIZONS)),
        np.array(columns[8], dtype=float).reshape(-1, len(HORIZONS)),
    )
