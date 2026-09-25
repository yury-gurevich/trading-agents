"""Plain-words rendering of the reporter's benchmark scoreboard.

Agent: surfaces
Role: round and word the scoreboard once, for the dashboard vital and the chat answer.
External I/O: none.

Rounding matches the reporter's headline (agents/reporter/snapshot_result.py): two
decimals for points and percent, whole percent for exposure, `-0.00` shown as `0.00`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from surfaces.queries.performance import PerformanceView

_MINUS = chr(0x2212)  # the typographic minus the operator reads
_MARKET = "the market"


def display(value: float) -> float:
    """Round to the two decimals the operator reads; -0.00 becomes 0.00."""
    rounded = float(f"{value:.2f}")
    return 0.0 if rounded == 0 else rounded


def signed(value: float) -> str:
    """Two-decimal number with a typographic minus, as the operator reads it."""
    shown = display(value)
    return f"{_MINUS}{abs(shown):.2f}" if shown < 0 else f"{shown:.2f}"


def vital_line(view: PerformanceView) -> str:
    """Return the status-line text, e.g. ``vs SPY -0.28 pts · 32 sessions``."""
    m = view.metrics
    return (
        f"vs {view.benchmark or _MARKET} {signed(m['excess_return_pct'])} pts · "
        f"{m['performance_sessions']:.0f} sessions · "
        f"{m['average_exposure_pct']:.0f} % invested"
    )


def detail_rows(view: PerformanceView) -> list[tuple[str, str]]:
    """Return the labelled numbers shown when the operator opens the vital."""
    m = view.metrics
    name = view.benchmark or _MARKET
    sessions = f"{m['performance_sessions']:.0f}"
    if m["performance_gap_sessions"]:
        sessions += f" ({m['performance_gap_sessions']:.0f} without a price)"
    return [
        ("Excess since inception", f"{signed(m['excess_return_pct'])} pts"),
        ("Excess, recent sessions", f"{signed(m['rolling_excess_return_pct'])} pts"),
        ("Book return", f"{signed(m['portfolio_return_pct'])} %"),
        (f"{name} return", f"{signed(m['benchmark_return_pct'])} %"),
        (
            f"{name} at the book's exposure",
            f"{signed(m['exposure_matched_return_pct'])} %",
        ),
        ("Average invested", f"{m['average_exposure_pct']:.0f} %"),
        ("Max drawdown", f"{signed(m['max_drawdown_pct'])} %"),
        ("Sessions counted", sessions),
        ("Equity", f"${m['equity_cents'] / 100:,.2f}"),
    ]


def summary(view: PerformanceView) -> str:
    """Return the one-paragraph chat answer for the run's scoreboard."""
    if view.status == "unavailable":
        subject = f" for run {view.run_id}" if view.run_id else " yet"
        return f"There is no scoreboard{subject}: {view.reason}."
    if view.status == "no_sessions":
        subject = f"The scoreboard for run {view.run_id}"
        return f"{subject} has no sessions yet: {view.reason}."
    m = view.metrics
    name = view.benchmark or _MARKET
    return (
        f"{_lead(m['excess_return_pct'])} over "
        f"{m['performance_sessions']:.0f} sessions: "
        f"the book returned {signed(m['portfolio_return_pct'])} %, "
        f"{name} {signed(m['benchmark_return_pct'])} %, and {name} at the book's "
        f"{m['average_exposure_pct']:.0f} % exposure "
        f"{signed(m['exposure_matched_return_pct'])} %. "
        f"Over the most recent sessions: {_recent(m['rolling_excess_return_pct'])}."
    )


def _lead(excess: float) -> str:
    shown = display(excess)
    if shown > 0:
        return f"Ahead of {_MARKET} by {shown:.2f} pts"
    if shown < 0:
        return f"Behind {_MARKET} by {abs(shown):.2f} pts"
    return f"Level with {_MARKET}"


def _recent(excess: float) -> str:
    shown = display(excess)
    if shown > 0:
        return f"ahead by {shown:.2f} pts"
    if shown < 0:
        return f"behind by {abs(shown):.2f} pts"
    return "level with it"
