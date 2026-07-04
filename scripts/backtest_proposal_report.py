"""Report formatting for researcher proposal backtests.

Agent: tooling
Role: render full-window and holdout backtest metrics as markdown.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.researcher.domain.backtest_types import BacktestResult


def render_table(incumbent: BacktestResult, proposed: BacktestResult) -> str:
    """Render full-window and holdout metrics side by side."""
    rows = [
        (
            "n_days",
            incumbent.n_days,
            proposed.n_days,
            incumbent.holdout_n_days,
            proposed.holdout_n_days,
        ),
        (
            "sharpe",
            incumbent.sharpe,
            proposed.sharpe,
            incumbent.holdout_sharpe,
            proposed.holdout_sharpe,
        ),
        (
            "ic_mean",
            incumbent.ic_mean,
            proposed.ic_mean,
            incumbent.holdout_ic_mean,
            proposed.holdout_ic_mean,
        ),
        (
            "max_drawdown",
            incumbent.max_drawdown,
            proposed.max_drawdown,
            incumbent.holdout_max_drawdown,
            proposed.holdout_max_drawdown,
        ),
        (
            "turnover",
            incumbent.turnover,
            proposed.turnover,
            incumbent.holdout_turnover,
            proposed.holdout_turnover,
        ),
    ]
    lines = [
        (
            "| metric | incumbent full | proposed full | delta | "
            "incumbent holdout | proposed holdout | holdout delta |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, inc_full, prop_full, inc_hold, prop_hold in rows:
        lines.append(
            "| "
            f"{name} | {_fmt(inc_full)} | {_fmt(prop_full)} | "
            f"{_fmt_delta(prop_full, inc_full)} | {_fmt(inc_hold)} | "
            f"{_fmt(prop_hold)} | {_fmt_delta(prop_hold, inc_hold)} |"
        )
    return "\n".join(lines)


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.6f}"


def _fmt_delta(value: float | int | None, baseline: float | int | None) -> str:
    if value is None or baseline is None:
        return "n/a"
    return _fmt(value - baseline)
