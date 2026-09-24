"""Shared fakes and graph setup for S219 dispatcher-answer tests.

Agent: orchestration
Role: provide deterministic dispatcher test inputs.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from agents.scanner.universe import FakeUniverse
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
from orchestration.telegram_updates import TelegramAnswer

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore
    from orchestration.scheduled_dispatch import ScheduledDispatchResult

AS_OF = date(2026, 7, 8)
NOW = datetime(2026, 9, 20, 22, 30, tzinfo=UTC)


FakeAnswer = TelegramAnswer


@dataclass
class FakeTelegram:
    """Telegram port fake that records every attempted operation."""

    answers: tuple[TelegramAnswer, ...] = ()
    fails: bool = False
    degraded_returns_none: bool = False
    sent: list[dict[str, object]] = field(default_factory=list)
    degraded_sent: list[dict[str, object]] = field(default_factory=list)
    acknowledgements: list[tuple[str, str]] = field(default_factory=list)
    confirmations: list[int] = field(default_factory=list)
    polls: int = 0

    def send_hold_notice(
        self, *, run_id: str, failures: tuple[str, ...], act_by: str
    ) -> int:
        self._raise_if_needed()
        self.sent.append({"run_id": run_id, "failures": failures, "act_by": act_by})
        return len(self.sent)

    def send_degraded_notice(
        self, *, run_id: str, failures: tuple[str, ...]
    ) -> int | None:
        self._raise_if_needed()
        self.degraded_sent.append({"run_id": run_id, "failures": failures})
        if self.degraded_returns_none:
            return None
        return len(self.degraded_sent)

    def poll_answers(self) -> tuple[TelegramAnswer, ...]:
        self._raise_if_needed()
        self.polls += 1
        return self.answers

    def ack_button(self, *, callback_query_id: str, text: str) -> bool:
        self._raise_if_needed()
        self.acknowledgements.append((callback_query_id, text))
        return True

    def confirm(self, *, up_to_update_id: int) -> bool:
        self._raise_if_needed()
        self.confirmations.append(up_to_update_id)
        return True

    def _raise_if_needed(self) -> None:
        if self.fails:
            raise TimeoutError("telegram unavailable")


def preflight(
    graph: InMemoryGraphStore,
    *,
    passed: bool,
    checked_at: datetime = NOW - timedelta(minutes=5),
    failures: tuple[str, ...] = (),
) -> None:
    """Append one master-owned readiness fact for the test run."""
    checked = checked_at.isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked}",
        {"checked_at": checked, "passed": passed, "failures": list(failures)},
    )


def active_hold(graph: InMemoryGraphStore, *, run_id: str = "sched-2026-07-08") -> None:
    """Append an active hold that makes answer polling applicable."""
    graph.merge_node(
        "RunHold",
        f"hold:{run_id}",
        {
            "run_id": run_id,
            "as_of": AS_OF.isoformat(),
            "held_at": NOW.isoformat(timespec="seconds"),
            "state": "held",
            "readiness_state": "failing",
            "preflight_key": "preflight:test",
            "failures": ["unrecoverable:provider:credential"],
        },
    )


def dispatch(
    graph: InMemoryGraphStore, telegram: FakeTelegram, *, as_of: date = AS_OF
) -> ScheduledDispatchResult:
    """Run the planned S219 controller through its public seam."""
    return dispatch_with_human_answer(
        graph,
        as_of=as_of,
        now=NOW,
        telegram=telegram,
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
    )
