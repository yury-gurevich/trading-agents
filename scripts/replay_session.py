"""Session loop for the S235 replay runner.

Agent: tooling
Role: advance replay sessions and collect broker, count, and equity outputs.
External I/O: none.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from scripts.replay_counters import replay_day_counts
from scripts.replay_day import ReplayDayInputs
from scripts.replay_ledger import (
    next_session,
    queue_orders,
    settle_pending,
    settle_stops,
)
from scripts.replay_marks import (
    apply_adjustment_rebases,
    exit_ended_positions,
    mark_positions,
)
from scripts.replay_outputs import EquityPoint
from scripts.replay_series import (
    benchmark_window,
    contract_bars,
    has_line_bar,
    held,
    held_stops,
    members_on,
    window_bars,
)
from scripts.replay_session_helpers import position_values, progress_line

from agents.execution.order_tolerance import OrderToleranceConfig
from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from scripts.replay_broker import PendingOrder, ReplayPosition
    from scripts.replay_cache import ReplayContext
    from scripts.replay_day import ReplayDayResult
    from scripts.replay_settings import ReplaySettings
    from scripts.sp500_bars import BarRow, KnownMove


@dataclass(frozen=True)
class ReplayLoopResult:
    absent: dict[str, Any]
    equity: tuple[EquityPoint, ...]
    fills: tuple[dict[str, Any], ...]
    session_rows: tuple[dict[str, Any], ...]


_CENTS = Decimal("100")


def run_replay_sessions(
    *,
    context: ReplayContext,
    settings: ReplaySettings,
    sessions: tuple[date, ...],
    line_bars: dict[str, tuple[BarRow, ...]],
    date_bars: dict[date, dict[str, BarRow]],
    fixed_lines: tuple[str, ...] | None,
    known_moves: dict[str, KnownMove],
    slippage_bps: int,
    absent: dict[str, Any],
    day_runner: Callable[[ReplayDayInputs, ReplaySettings], ReplayDayResult],
    progress_every: int,
) -> ReplayLoopResult:
    """Run the replay sessions and return byte-stable output rows."""
    pending: list[PendingOrder] = []
    positions: dict[str, ReplayPosition] = {}
    cash_cents = int(settings.portfolio.starting_cash * _CENTS)
    equity: list[EquityPoint] = []
    fills: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    total = len(sessions)
    for index, session in enumerate(sessions):
        day_bars = date_bars.get(session, {})
        rebased = apply_adjustment_rebases(session, positions, line_bars, known_moves)
        absent["adjustment_error_rebases"] += rebased.count
        cash_cents += settle_stops(
            day_bars, positions, fills, slippage_bps, skip_lines=rebased.lines
        )
        pending_result = settle_pending(
            session,
            next_session(sessions, index),
            pending,
            day_bars,
            positions,
            fills,
            slippage_bps,
        )
        cash_cents += pending_result.cash_delta_cents
        absent["expired_no_bar"] += pending_result.no_bar
        pending = [order for order in pending if order.target_session > session]
        exits = exit_ended_positions(
            session, positions, line_bars, context.universe.episodes, fills
        )
        cash_cents += exits.cash_delta_cents
        absent["data_end_exits"] += exits.data_end_exits
        absent["membership_end_exits"] += exits.membership_end_exits
        members = fixed_lines or members_on(context.universe, session)
        visible_bars = _visible_bars(settings, line_bars, members, session)
        if fixed_lines is not None:
            members = tuple(
                line for line in members if has_line_bar(visible_bars, line)
            )
        vix = context.vix.get(session)
        absent["sessions_without_vix"] += int(vix is None)
        absent["member_sessions_without_sector"] += sum(
            1 for line in members if not context.sectors.get(line)
        )
        marked = mark_positions(cash_cents, positions, line_bars, session)
        absent["gap_marks"] += marked.gap_marks
        result = day_runner(
            ReplayDayInputs(
                run_id=f"replay-{session.isoformat()}",
                session=session,
                tickers=members,
                bars=contract_bars(visible_bars),
                benchmark_bars=benchmark_window(
                    context.benchmark, session, visible_bars
                ),
                vix=vix,
                equity_cents=marked.equity_cents,
                held=held(positions),
                held_stops=held_stops(positions),
                active_broker_stop_refs=frozenset(
                    position.position_ref for position in positions.values()
                ),
                sectors=context.sectors,
                position_values=position_values(positions, line_bars, session),
            ),
            settings,
        )
        for key, value in result.absent_inputs.items():
            absent[key] = int(absent.get(key, 0)) + value
        absent["buy_without_stop"] += queue_orders(
            result.approved,
            sessions,
            index,
            pending,
            OrderToleranceConfig.from_settings(settings.execution),
        )
        equity.append(EquityPoint(session, marked.equity_cents, marked.long_cents))
        session_rows.append(
            {
                "date": session.isoformat(),
                "expired": pending_result.expired,
                "expired_no_bar": pending_result.no_bar,
                "gap_marks": marked.gap_marks,
                **replay_day_counts(members, result),
            }
        )
        progress_line(
            session.isoformat(),
            index + 1,
            total,
            marked.equity_cents,
            started,
            progress_every,
        )
    return ReplayLoopResult(absent, tuple(equity), tuple(fills), tuple(session_rows))


def _visible_bars(
    settings: ReplaySettings,
    line_bars: dict[str, tuple[BarRow, ...]],
    members: tuple[str, ...],
    session: date,
) -> tuple[BarRow, ...]:
    lookback_days = declared_lookback_days(
        settings.analyst,
        as_of=session,
        staleness_buffer_sessions=settings.provider.max_staleness_days,
    )
    return window_bars(line_bars, members, session, lookback_days)
