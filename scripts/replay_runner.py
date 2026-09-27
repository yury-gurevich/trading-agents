"""Run the S235 replay loop over cached fixture data.

Agent: tooling
Role: advance sessions, call fleet stages, simulate broker fills, and summarize.
External I/O: writes deterministic replay artifacts outside the worktree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.replay_cache import load_replay_cache
from scripts.replay_counters import initial_absent_inputs
from scripts.replay_day import run_replay_day
from scripts.replay_outputs import (
    performance_summary,
    refuse_worktree_out,
    write_replay_outputs,
)
from scripts.replay_series import (
    bars_by_date,
    bars_by_line,
    bounded_sessions,
    read_universe_file,
)
from scripts.replay_session import run_replay_sessions
from scripts.replay_settings import build_effective_settings
from scripts.sp500_guards import load_known_moves

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

DEFAULT_SLIPPAGE_BPS = 10
DEFAULT_PROGRESS_EVERY = 20


def run(
    *,
    cache_dir: Path,
    out: Path | None,
    start: date | None,
    end: date | None,
    overrides: tuple[str, ...],
    slippage_bps: int = DEFAULT_SLIPPAGE_BPS,
    universe_file: Path | None = None,
    progress_every: int = DEFAULT_PROGRESS_EVERY,
) -> dict[str, Any]:
    """Run a deterministic replay and write artifacts under the cache directory."""
    context = load_replay_cache(cache_dir)
    settings = build_effective_settings(overrides)
    sessions = bounded_sessions(context.universe.sessions, start, end)
    line_bars = bars_by_line(context.universe.bars)
    date_bars = bars_by_date(context.universe.bars)
    fixed_lines = read_universe_file(universe_file) if universe_file else None
    known_moves = load_known_moves()
    loop = run_replay_sessions(
        context=context,
        settings=settings,
        sessions=sessions,
        line_bars=line_bars,
        date_bars=date_bars,
        fixed_lines=fixed_lines,
        known_moves=known_moves,
        slippage_bps=slippage_bps,
        absent=initial_absent_inputs(),
        day_runner=run_replay_day,
        progress_every=progress_every,
    )
    summary = {
        "performance": performance_summary(loop.equity, context.spy_closes),
        "non_default_settings": settings.non_defaults,
        "absent_inputs": loop.absent,
    }
    write_replay_outputs(
        refuse_worktree_out(out or cache_dir / "pipeline-replay"),
        loop.equity,
        loop.fills,
        loop.session_rows,
        summary,
    )
    return summary
