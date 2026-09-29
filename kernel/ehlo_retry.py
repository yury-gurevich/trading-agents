"""Resend one EHLO until master answers, inside a bounded budget.

Agent: kernel
Role: classify a failed EHLO send as transient or final, and resend the transient
      ones with exponential backoff and full jitter, reusing the caller's body (one
      boot id) until the attempt cap or the total budget is spent (DL-249 D1/D2).
External I/O: none directly (the sender is injected); one stderr line per failure.
"""

from __future__ import annotations

import http.client
import random
import sys
import time
import urllib.error
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel.ehlo_settings import EhloSettings

    Sender = Callable[[str, dict[str, object], float], dict[str, object]]

_TRANSIENT_STATUSES = frozenset({502, 503, 504})
_TRANSIENT_ERRORS: tuple[type[BaseException], ...] = (
    TimeoutError,
    ConnectionRefusedError,
    ConnectionResetError,
    ConnectionAbortedError,
    http.client.RemoteDisconnected,
)
_MIN_ATTEMPT_TIMEOUT_SECONDS = 1.0


class EhloBudgetExhaustedError(RuntimeError):
    """Every EHLO attempt this boot was allowed failed transiently (``MST-FAIL-06``)."""

    def __init__(
        self, url: str, attempts: int, elapsed_seconds: float, last_cause: BaseException
    ) -> None:
        """Name the attempts, the elapsed time and the last cause in one line."""
        self.attempts = attempts
        self.elapsed_seconds = elapsed_seconds
        self.last_cause = last_cause
        super().__init__(
            f"EHLO to {url} failed after {attempts} attempt(s) in "
            f"{elapsed_seconds:.1f}s; last cause: {_describe(last_cause)}"
        )


def _stderr(line: str) -> None:
    sys.stderr.write(f"{line}\n")
    sys.stderr.flush()


@dataclass(frozen=True)
class RetryHooks:
    """The loop's clock, sleep, jitter source and log line sink — injectable."""

    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    rand: Callable[[], float] = random.random
    log: Callable[[str], None] = _stderr


def is_transient(exc: BaseException) -> bool:
    """Return True only for a transport failure worth resending (DL-249 D2).

    ``HTTPError`` is a ``URLError``: its status decides first (502/503/504 resend,
    any other status is master's answer). A ``URLError`` resends only when its
    reason is a transport failure; a 4xx, a bad signature or a DNS error is final.
    """
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _TRANSIENT_STATUSES
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        return isinstance(reason, BaseException) and is_transient(reason)
    return isinstance(exc, _TRANSIENT_ERRORS)


def backoff_delay(
    attempt: int, settings: EhloSettings, rand: Callable[[], float]
) -> float:
    """Full jitter: uniform below ``min(cap, base * 2^(attempt-1))``."""
    ceiling = min(
        settings.ehlo_backoff_cap_seconds,
        settings.ehlo_backoff_base_seconds * 2.0 ** (attempt - 1),
    )
    return rand() * ceiling


def send_with_retry(
    send: Sender,
    url: str,
    body: dict[str, object],
    settings: EhloSettings,
    hooks: RetryHooks,
) -> dict[str, object]:
    """POST *body* to *url*, resending transient failures within the budget.

    The same *body* (one ``ephemeral_boot_id``) goes out on every attempt, so master
    replays rather than re-activates (``MST-IDM-03``). A final failure propagates on
    the attempt that met it; a spent budget raises ``EhloBudgetExhaustedError``.
    """
    started = hooks.clock()
    attempt = 0
    while True:
        attempt += 1
        remaining = settings.ehlo_budget_seconds - (hooks.clock() - started)
        timeout = min(
            settings.ehlo_attempt_timeout_seconds,
            max(remaining, _MIN_ATTEMPT_TIMEOUT_SECONDS),
        )
        try:
            return send(url, body, timeout)
        except Exception as exc:
            if not is_transient(exc):
                raise
            cause = exc
        elapsed = hooks.clock() - started
        delay = backoff_delay(attempt, settings, hooks.rand)
        spent = (
            attempt >= settings.ehlo_max_attempts
            or elapsed + delay >= settings.ehlo_budget_seconds
        )
        hooks.log(
            f"[ehlo] attempt {attempt}/{settings.ehlo_max_attempts} to {url} failed "
            f"after {elapsed:.1f}s: {_describe(cause)}; "
            + ("budget spent" if spent else f"resending in {delay:.1f}s")
        )
        if spent:
            raise EhloBudgetExhaustedError(url, attempt, elapsed, cause) from cause
        hooks.sleep(delay)


def _describe(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"
