"""Run the S235 replay loop over cached fixture data.

Agent: tooling
Role: advance sessions, call fleet stages, simulate broker fills, and summarize.
External I/O: writes deterministic replay artifacts outside the worktree.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from scripts.replay_cache import load_replay_cache
from scripts.replay_day import ReplayDayInputs, run_replay_day
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
from scripts.replay_outputs import (
    EquityPoint,
    performance_summary,
    refuse_worktree_out,
    write_replay_outputs,
)
from scripts.replay_series import (
    bars_by_date,
    bars_by_line,
    benchmark_window,
    bounded_sessions,
    contract_bars,
    has_line_bar,
    held,
    held_stops,
    members_on,
    read_universe_file,
    window_bars,
)
from scripts.replay_settings import build_effective_settings
from scripts.sp500_guards import load_known_moves

from agents.execution.order_tolerance import OrderToleranceConfig
from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

    from scripts.replay_broker import PendingOrder, ReplayPosition

DEFAULT_SLIPPAGE_BPS = 10
_CENTS = Decimal("100")


def run(
    *,
    cache_dir: Path,
    out: Path | None,
    start: date | None,
    end: date | None,
    overrides: tuple[str, ...],
    slippage_bps: int = DEFAULT_SLIPPAGE_BPS,
    universe_file: Path | None = None,
) -> dict[str, Any]:
    """Run a deterministic replay and write artifacts under the cache directory."""
    context = load_replay_cache(cache_dir)
    settings = build_effective_settings(overrides)
    sessions = bounded_sessions(context.universe.sessions, start, end)
    line_bars = bars_by_line(context.universe.bars)
    date_bars = bars_by_date(context.universe.bars)
    fixed_lines = read_universe_file(universe_file) if universe_file else None
    known_moves = load_known_moves()
    pending: list[PendingOrder] = []
    positions: dict[str, ReplayPosition] = {}
    cash_cents = int(settings.portfolio.starting_cash * _CENTS)
    equity: list[EquityPoint] = []
    fills: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []
    absent: dict[str, Any] = {
        "fundamentals": 0,
        "news": 0,
        "sentiment": 0,
        "earnings": 0,
        "deliberator": 0,
        "pillars_present": ["technical", "relative_strength"],
        "member_sessions_without_sector": 0,
        "sessions_without_vix": 0,
        "gap_marks": 0,
        "adjustment_error_rebases": 0,
        "data_end_exits": 0,
        "membership_end_exits": 0,
        "expired_no_bar": 0,
        "buy_without_stop": 0,
    }
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
        lookback_days = declared_lookback_days(
            settings.analyst,
            as_of=session,
            staleness_buffer_sessions=settings.provider.max_staleness_days,
        )
        visible_bars = window_bars(
            line_bars,
            members,
            session,
            lookback_days,
        )
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
        result = run_replay_day(
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
            }
        )
    summary = {
        "performance": performance_summary(tuple(equity), context.spy_closes),
        "non_default_settings": settings.non_defaults,
        "absent_inputs": absent,
    }
    write_replay_outputs(
        refuse_worktree_out(out or cache_dir / "pipeline-replay"),
        tuple(equity),
        tuple(fills),
        tuple(session_rows),
        summary,
    )
    return summary
