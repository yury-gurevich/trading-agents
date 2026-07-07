"""Calendar-gated scheduled RunRequest placement.

Agent: orchestration
Role: decide whether a scheduled daily run should place the graph-pull trigger.
External I/O: writes only the injected GraphStore.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from agents.provider.domain.market_calendar import (
    calendar_window_end,
    is_trading_session,
)
from agents.scanner.universe import StaticUniverse
from orchestration.settings import OrchestratorSettings
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from datetime import date

    from agents.scanner.universe import UniverseSource
    from kernel import GraphStore


class CalendarWindowExceededError(ValueError):
    """Raised when scheduling asks beyond the known NYSE calendar window."""


class TradingCalendar(Protocol):
    """Small calendar port used by scheduled placement."""

    def is_trading_session(self, day: date) -> bool:
        """Return whether *day* is a trading session."""
        ...  # pragma: no cover - protocol declaration only.

    def window_end(self) -> date:
        """Return the final date covered by the calendar."""
        ...  # pragma: no cover - protocol declaration only.


class ProviderTradingCalendar:
    """Adapter over the provider-owned NYSE session calendar."""

    def is_trading_session(self, day: date) -> bool:
        """Return whether *day* is a provider-known NYSE trading session."""
        return is_trading_session(day)

    def window_end(self) -> date:
        """Return the provider calendar's explicit coverage end date."""
        return calendar_window_end()


@dataclass(frozen=True)
class ScheduledDispatchDecision:
    """Pure scheduled-run decision before touching the graph."""

    action: Literal["place", "skip"]
    run_id: str
    reason: str


@dataclass(frozen=True)
class ScheduledDispatchResult:
    """Scheduled-run outcome after optional graph placement."""

    action: Literal["placed", "skipped"]
    run_id: str
    reason: str
    node_key: str | None = None
    tickers: tuple[str, ...] = ()


_PROVIDER_CALENDAR = ProviderTradingCalendar()


def scheduled_run_id(day: date) -> str:
    """Return the deterministic day-keyed scheduled run id."""
    return f"sched-{day.isoformat()}"


def decide_scheduled_run(
    as_of: date, *, calendar: TradingCalendar = _PROVIDER_CALENDAR
) -> ScheduledDispatchDecision:
    """Return whether the scheduler should place a run for *as_of*."""
    run_id = scheduled_run_id(as_of)
    end = calendar.window_end()
    if as_of > end:
        raise CalendarWindowExceededError(
            f"{as_of.isoformat()} is beyond the NYSE calendar window ending "
            f"{end.isoformat()}"
        )
    if not calendar.is_trading_session(as_of):
        return ScheduledDispatchDecision(
            "skip", run_id, f"{as_of.isoformat()} is not a NYSE trading session"
        )
    return ScheduledDispatchDecision("place", run_id, "NYSE trading session")


def place_scheduled_run(
    graph: GraphStore,
    *,
    as_of: date,
    calendar: TradingCalendar = _PROVIDER_CALENDAR,
    settings: OrchestratorSettings | None = None,
    universe_source: UniverseSource | None = None,
) -> ScheduledDispatchResult:
    """Place the scheduled RunRequest, or cleanly skip non-trading sessions."""
    decision = decide_scheduled_run(as_of, calendar=calendar)
    if decision.action == "skip":
        return ScheduledDispatchResult("skipped", decision.run_id, decision.reason)

    active_settings = settings or OrchestratorSettings()
    source = universe_source or StaticUniverse()
    tickers = source.members(active_settings.universe)
    if not tickers:
        raise ValueError(f"universe {active_settings.universe!r} has no tickers")

    node = place_run_request(
        graph, run_id=decision.run_id, tickers=tickers, as_of=as_of
    )
    return ScheduledDispatchResult(
        "placed", decision.run_id, decision.reason, node.key, tickers
    )
