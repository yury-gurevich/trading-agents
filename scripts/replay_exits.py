"""Exit policies a replay arm can declare beside its protective stops (S281).

Agent: tooling
Role: hold one arm's exit policy and apply it in the session loop: time exits,
      trailing stops and the re-entry cool-down (the take-profit rests in the broker).
External I/O: none.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from scripts.replay_ledger import queue_orders, replay_bar

from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent
from contracts.stop_rule import stop_price_cents

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date

    from scripts.replay_broker import PendingOrder, ReplayPosition
    from scripts.sp500_bars import BarRow

    from agents.execution.order_tolerance import OrderToleranceConfig

TIME_EXIT = "time_exit"
COUNT_KEYS = (
    "buy_without_target",
    "cooldown_member_sessions",
    "time_exit_orders",
    "trail_raises",
)


def _whole(value: object, floor: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= floor


@dataclass(frozen=True)
class ExitPolicy:
    """How an arm's positions leave the book besides their stop; all off by default."""

    take_profit: bool = False
    time_exit_sessions: int | None = None
    trailing_stop: bool = False
    reentry_cooldown_sessions: int = 0

    def __post_init__(self) -> None:
        for name in ("take_profit", "trailing_stop"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be true or false")
        sessions = self.time_exit_sessions
        if sessions is not None and not _whole(sessions, 1):
            raise ValueError("time_exit_sessions must be a whole number, at least 1")
        if not _whole(self.reentry_cooldown_sessions, 0):
            raise ValueError("reentry_cooldown_sessions must be a whole number, >= 0")

    @property
    def declared(self) -> bool:
        """Whether the arm asks for anything beyond stops only."""
        return self != ExitPolicy()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


STOPS_ONLY = ExitPolicy()


def exit_policy_from(data: Mapping[str, Any] | None) -> ExitPolicy:
    """Read a manifest arm's `exits`; absent is stops only, an unknown key refused."""
    if data is None:
        return STOPS_ONLY
    known = tuple(STOPS_ONLY.as_dict())
    unknown = sorted(set(data) - set(known))
    if unknown:
        raise ValueError(f"unknown exit keys {unknown}; known: {', '.join(known)}")
    return ExitPolicy(**data)


@dataclass
class ExitState:
    """One run's exit bookkeeping: the lines cooling down and the counts."""

    policy: ExitPolicy
    cooling: dict[str, int] = field(default_factory=dict)
    counts: Counter[str] = field(default_factory=Counter)

    def note_stops(self, new_fills: list[dict[str, Any]]) -> None:
        """Start the cool-down for each line whose stop filled this session."""
        for row in new_fills:
            if self.policy.reentry_cooldown_sessions and row["reason"] == "stop":
                self.cooling[row["line"]] = self.policy.reentry_cooldown_sessions

    def cool(self, members: tuple[str, ...]) -> tuple[str, ...]:
        """Leave cooling lines out of this session's run, then count one session."""
        kept = tuple(line for line in members if line not in self.cooling)
        self.counts["cooldown_member_sessions"] += len(members) - len(kept)
        self.cooling = {line: n - 1 for line, n in self.cooling.items() if n > 1}
        return kept

    def raise_stops(
        self,
        session: date,
        positions: dict[str, ReplayPosition],
        day_bars: Mapping[str, BarRow],
    ) -> None:
        """Lift each active stop to the session's high less its stop percent."""
        if not self.policy.trailing_stop:
            return
        for line, position in tuple(positions.items()):
            row = day_bars.get(line)
            if row is None or session < position.stop_active_from:
                continue
            raised = stop_price_cents(replay_bar(row).high_cents, position.stop_pct)
            if raised > position.stop_price_cents:
                positions[line] = replace(position, stop_price_cents=raised)
                self.counts["trail_raises"] += 1

    def queue_orders(
        self,
        index: int,
        sessions: tuple[date, ...],
        positions: dict[str, ReplayPosition],
        pending: list[PendingOrder],
        day_bars: Mapping[str, BarRow],
        approved: tuple[Any, ...],
        config: OrderToleranceConfig,
    ) -> int:
        """Queue the PM's intents, then the time exits; return the stopless buys.

        With a take-profit, a buy carries its target and a targetless one is counted;
        with a time exit, what has held N sessions and has no sell waiting is sold at
        the next session.
        """
        stopless = queue_orders(
            approved,
            sessions,
            index,
            pending,
            config,
            take_profit=self.policy.take_profit,
        )
        if self.policy.take_profit:
            self.counts["buy_without_target"] += sum(
                1
                for intent in approved
                if intent.action == "buy"
                and intent.stop_pct is not None
                and intent.target_pct is None
            )
        limit = self.policy.time_exit_sessions
        if limit is None or index + 1 >= len(sessions):
            return stopless
        selling = {order.line for order in pending if order.side == "sell"}
        intents = tuple(
            _time_exit(line, position, day_bars[line], limit)
            for line, position in sorted(positions.items())
            if line not in selling
            and line in day_bars
            and held_sessions(sessions, position.opened, index) >= limit
        )
        self.counts["time_exit_orders"] += len(intents)
        queue_orders(intents, sessions, index, pending, config, reason=TIME_EXIT)
        return stopless

    def summary(self) -> dict[str, Any] | None:
        """The policy and its counts, or None for a stops-only arm."""
        if not self.policy.declared:
            return None
        counts = {key: self.counts[key] for key in COUNT_KEYS}
        return {"counts": counts, "policy": self.policy.as_dict()}


def held_sessions(sessions: tuple[date, ...], opened: date, index: int) -> int:
    """Sessions a position has closed in the book by `sessions[index]`, its first 1."""
    return index - bisect_left(sessions, opened) + 1


def _time_exit(
    line: str, position: ReplayPosition, row: BarRow, limit: int
) -> OrderIntent:
    return OrderIntent(
        ticker=line,
        action="sell",
        quantity=position.quantity,
        est_price=Money(amount=Decimal(str(row.close))),
        position_ref=position.position_ref,
        rationale=Explanation(summary=f"time exit after {limit} sessions"),
    )
