"""Replay a resent EHLO: one boot id is one activation (``MST-IDM-03``).

Agent: master
Role: remember the signed ACTIVATE answered for each ephemeral boot id for a bounded
      lifetime, hand the same answer to a resend of the same agent type, refuse the
      boot id to any other type, and make concurrent duplicates wait for the first
      (DL-249 D3). A refusal or an error is never remembered.
External I/O: none (in-process memory; master has one replica).
"""

from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.master.settings import MasterSettings

Answer = dict[str, object]


class ReplayConflictError(ValueError):
    """A boot id already activated as one agent type was presented as another."""


@dataclass
class _Entry:
    agent_type: str
    done: threading.Event = field(default_factory=threading.Event)
    answer: Answer | None = None
    stored_at: float = 0.0


def replay_lifetime_seconds(settings: MasterSettings) -> float:
    """The replay window, capped by the credential-pass and secret-cache TTLs.

    A replay re-delivers credentials without a re-test, so it never outlives the
    pass or the fetched value it was built on (``MST-NEV-06``); a TTL of 0 means
    "never expires" and caps nothing.
    """
    ttls = (
        settings.credential_pass_cache_ttl_minutes,
        settings.secret_cache_ttl_minutes,
    )
    return min(
        [settings.handshake_timeout_2_seconds, *(60.0 * ttl for ttl in ttls if ttl > 0)]
    )


class ActivationReplay:
    """Thread-safe boot-id → signed ACTIVATE store with an in-flight guard."""

    def __init__(
        self, lifetime_seconds: float, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        """Remember each answer for *lifetime_seconds* on *clock* (monotonic)."""
        self._lifetime = lifetime_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: dict[str, _Entry] = {}

    def answer(
        self, boot_id: str, agent_type: str, mint: Callable[[], Answer]
    ) -> Answer:
        """Return the stored answer for *boot_id*, or mint it exactly once.

        Raises ``ReplayConflictError`` (a 422) when *boot_id* belongs to another
        agent type; a failing *mint* leaves nothing, so a later resend tries afresh.
        """
        while True:
            with self._lock:
                self._purge_expired()
                entry = self._entries.get(boot_id)
                if entry is None:
                    entry = self._entries[boot_id] = _Entry(agent_type)
                    break
                if entry.agent_type != agent_type:
                    raise ReplayConflictError(
                        f"boot id {boot_id!r} is already bound to another agent type"
                    )
                if entry.answer is not None:
                    return copy.deepcopy(entry.answer)
                in_flight = entry.done
            in_flight.wait(self._lifetime)
        return self._mint(boot_id, entry, mint)

    def _mint(self, boot_id: str, entry: _Entry, mint: Callable[[], Answer]) -> Answer:
        try:
            result = mint()
        except BaseException:
            with self._lock:  # in flight, so never purged: still this entry
                del self._entries[boot_id]
            entry.done.set()
            raise
        with self._lock:
            entry.answer = copy.deepcopy(result)
            entry.stored_at = self._clock()
        entry.done.set()
        return result

    def _purge_expired(self) -> None:
        now = self._clock()
        expired = [
            boot_id
            for boot_id, entry in self._entries.items()
            if entry.answer is not None and now - entry.stored_at >= self._lifetime
        ]
        for boot_id in expired:
            del self._entries[boot_id]
