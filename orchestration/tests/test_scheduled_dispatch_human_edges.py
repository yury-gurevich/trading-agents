"""Edge coverage for answer-aware scheduled dispatch helpers.

Agent: orchestration
Role: prove override boundaries and fault degradation for human answers.
External I/O: none; uses an in-memory graph and injected fakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import pytest

from agents.scanner.universe import FakeUniverse
from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch_actions import place_override, place_scheduled
from orchestration.scheduled_dispatch_polling import fault_safe

if TYPE_CHECKING:
    from orchestration.telegram_updates import TelegramAnswer

_AS_OF = date(2026, 7, 8)
_NOW = datetime(2026, 7, 8, 22, 30, tzinfo=UTC)


@dataclass(frozen=True)
class _SessionCalendar:
    def is_trading_session(self, _day: date) -> bool:
        return True

    def window_end(self) -> date:
        return _AS_OF


@dataclass
class _TelegramWithError:
    last_error: str = "telegram response invalid"

    def send_hold_notice(
        self, *, run_id: str, failures: tuple[str, ...], act_by: str
    ) -> int | None:
        return None

    def send_degraded_notice(
        self, *, run_id: str, failures: tuple[str, ...]
    ) -> int | None:
        return None

    def poll_answers(self) -> tuple[TelegramAnswer, ...]:
        return ()

    def ack_button(self, *, callback_query_id: str, text: str) -> bool:
        return False

    def confirm(self, *, up_to_update_id: int) -> bool:
        return False


def test_place_override_rejects_empty_universe() -> None:
    """DSP-IN-02 / DSP-FAIL-02: a run-now override cannot place an empty universe."""
    with pytest.raises(ValueError, match="has no tickers"):
        place_override(
            InMemoryGraphStore(),
            run_id="sched-2026-07-08",
            as_of=_AS_OF,
            reason="operator",
            settings=None,
            universe_source=FakeUniverse({"sp500": ()}),
        )


def test_place_scheduled_passes_the_injected_calendar() -> None:
    """S219: the normal scheduling path accepts an explicit session calendar."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "FleetPreflight",
        "preflight:passing",
        {"checked_at": _NOW.isoformat(), "passed": True, "failures": []},
    )

    result = place_scheduled(
        graph,
        as_of=_AS_OF,
        now=_NOW,
        calendar=_SessionCalendar(),
        settings=None,
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
    )

    assert result.action == "placed"


def test_fault_safe_records_port_reported_error() -> None:
    """DSP-FAIL-01: a falsy Telegram result with last_error becomes a graph fault."""
    graph = InMemoryGraphStore()

    result = fault_safe(graph, _TelegramWithError(), lambda: "ignored", "fallback")

    assert result == "fallback"
    assert graph.list_nodes("Fault")
