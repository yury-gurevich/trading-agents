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
    equity_cents,
    next_session,
    queue_orders,
    settle_pending,
    settle_stops,
)
from scripts.replay_outputs import (
    EquityPoint,
    performance_summary,
    refuse_worktree_out,
    write_replay_outputs,
)
from scripts.replay_series import (
    bars_by_line,
    benchmark_window,
    bounded_sessions,
    contract_bars,
    held,
    held_stops,
    members_on,
    window_bars,
)
from scripts.replay_settings import build_effective_settings

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
) -> dict[str, Any]:
    """Run a deterministic replay and write artifacts under the cache directory."""
    context = load_replay_cache(cache_dir)
    settings = build_effective_settings(overrides)
    sessions = bounded_sessions(context.universe.sessions, start, end)
    line_bars = bars_by_line(context.universe.bars)
    pending: list[PendingOrder] = []
    positions: dict[str, ReplayPosition] = {}
    cash_cents = int(settings.portfolio.starting_cash * _CENTS)
    equity: list[EquityPoint] = []
    fills: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []
    absent = dict.fromkeys(
        ("fundamentals", "news", "sentiment", "earnings", "deliberator"), 0
    )
    for index, session in enumerate(sessions):
        day_bars = {
            row.line: row for row in context.universe.bars if row.date == session
        }
        cash_cents += settle_stops(day_bars, positions, fills, slippage_bps)
        expired, cash_delta = settle_pending(
            session,
            next_session(sessions, index),
            pending,
            day_bars,
            positions,
            fills,
            slippage_bps,
        )
        cash_cents += cash_delta
        pending = [order for order in pending if order.target_session > session]
        members = members_on(context.universe, session)
        visible_bars = window_bars(
            line_bars,
            members,
            session,
            declared_lookback_days(
                settings.analyst,
                as_of=session,
                staleness_buffer_sessions=settings.provider.max_staleness_days,
            ),
        )
        result = run_replay_day(
            ReplayDayInputs(
                run_id=f"replay-{session.isoformat()}",
                session=session,
                tickers=members,
                bars=contract_bars(visible_bars),
                benchmark_bars=benchmark_window(
                    context.benchmark, session, visible_bars
                ),
                vix=context.vix.get(session),
                equity_cents=equity_cents(cash_cents, positions, day_bars),
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
            absent[key] += value
        queue_orders(
            result.approved,
            sessions,
            index,
            pending,
            OrderToleranceConfig.from_settings(settings.execution),
        )
        current_equity = equity_cents(cash_cents, positions, day_bars)
        equity.append(EquityPoint(session, current_equity, current_equity - cash_cents))
        session_rows.append({"date": session.isoformat(), "expired": expired})
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
