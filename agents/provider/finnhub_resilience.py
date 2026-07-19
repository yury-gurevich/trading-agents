"""Finnhub pacing and per-ticker degradation helpers.

Agent: provider
Role: keep Finnhub free-tier calls paced and attribute optional-feed failures.
External I/O: none directly; callers inject clock/sleep for real time or tests.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from contracts.feed_notes import format_degraded_feed_note

if TYPE_CHECKING:
    from collections.abc import Callable

_SECONDS_PER_MINUTE = 60.0
T = TypeVar("T")


class RequestRateBudget:
    """Sliding-window request budget; ``0`` disables pacing."""

    def __init__(
        self,
        requests_per_minute: int,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        """Create a budget with injectable clock/sleep for fast deterministic tests."""
        self._limit = max(0, requests_per_minute)
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._hits: deque[float] = deque()

    def wait(self) -> None:
        """Sleep only when the next request would exceed the active minute budget."""
        if self._limit == 0:
            return
        now = self._clock()
        self._prune(now)
        if len(self._hits) >= self._limit:
            oldest = self._hits[0]
            wait_for = max(0.0, _SECONDS_PER_MINUTE - (now - oldest))
            self._sleep(wait_for)
            now = self._clock()
            self._prune(now)
        self._hits.append(now)

    def _prune(self, now: float) -> None:
        while self._hits and now - self._hits[0] >= _SECONDS_PER_MINUTE:
            self._hits.popleft()


@dataclass(frozen=True)
class _TickerFailure:
    ticker: str
    error_label: str


class FeedFailureCollector:
    """Collect per-ticker failures for one optional Finnhub feed."""

    def __init__(self, feed: str, *, ticker_cap: int) -> None:
        """Create a collector for one named feed and bounded note detail."""
        self._feed = feed
        self._ticker_cap = ticker_cap
        self._failures: list[_TickerFailure] = []

    def capture(self, ticker: str, action: Callable[[str], T]) -> T | None:
        """Run one ticker action, returning ``None`` when that ticker failed."""
        try:
            return action(ticker)
        except Exception as exc:
            self._failures.append(_TickerFailure(ticker, _error_label(exc)))
            return None

    def note(self) -> str | None:
        """Return the bounded feed note for collected failures, if any."""
        if not self._failures:
            return None
        tickers = tuple(failure.ticker for failure in self._failures)
        return format_degraded_feed_note(
            self._feed,
            tickers,
            self._failures[0].error_label,
            self._ticker_cap,
        )


def _error_label(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return str(code)
    return type(exc).__name__
