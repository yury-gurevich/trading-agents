"""A role's handed-over LLM candidates, in order, and the move to the next (DL-289 P3).

Agent: deliberator
Role: hold one client per candidate the master handed the role; move the process to
      the next candidate when a vendor answers a request with an error status.
External I/O: none directly (the vendor clients it builds make the calls).

The master hands a role its chosen candidate under the role's three keys and each
later candidate that also passed under ``DELIBERATOR_LLM_FALLBACKS``, with its
vendor's key (`MST-OUT-05`). A vendor that answers with an HTTP error status
generated nothing, so the request is sent to the next candidate and the process
stays on it (`DLIB-FAIL-05`). A time-out or a dropped connection has no status: the
call's fate is unknown and its time is spent, so it fails the request as before.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.llm_factory import build_llm, key_env_var

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from agents.deliberator.settings import DeliberatorSettings
    from kernel.llm import LLMClient

_ERROR_STATUSES = range(400, 600)


@dataclass(frozen=True)
class RoleCandidate:
    """One handed-over way to run the role: its label, its model and its client."""

    label: str
    model: str
    client: LLMClient


class ModelChain:
    """The role's candidates in hand-over order; the process runs on one at a time.

    Shared by the manager's concurrent orders: a request refused by a candidate the
    process has already left is sent to the one in use, so two refusals of one
    candidate move the process once.
    """

    def __init__(self, candidates: Sequence[RoleCandidate]) -> None:
        """Hold the candidates, the first in use."""
        if not candidates:
            raise ValueError("a role needs at least one LLM candidate")
        self.candidates = tuple(candidates)
        self._index = 0
        self._lock = threading.Lock()

    def current(self) -> RoleCandidate:
        """Return the candidate the process is on."""
        with self._lock:
            return self.candidates[self._index]

    def after(self, refused: RoleCandidate) -> RoleCandidate | None:
        """Move past *refused* and return the candidate to send to; None at the end."""
        with self._lock:
            position = self.candidates.index(refused)
            if position + 1 >= len(self.candidates):
                return None
            self._index = max(self._index, position + 1)
            return self.candidates[self._index]


def refusal(exc: BaseException) -> str | None:
    """Name a vendor's error answer as ``http_<status>``, else None.

    Both SDKs give an API status error the HTTP status as ``status_code``. A
    time-out, a dropped connection, a truncated completion or an unreadable turn
    carries none.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, bool) or not isinstance(status, int):
        return None
    return f"http_{status}" if status in _ERROR_STATUSES else None


def handed_fallbacks(settings: DeliberatorSettings) -> tuple[tuple[str, str, str], ...]:
    """Return the fallbacks the master handed over, each vendor, model and effort."""
    found: list[tuple[str, str, str]] = []
    for item in settings.llm_fallbacks.split(","):
        text = item.strip()
        if not text:
            continue
        parts = text.split("/")
        if len(parts) != 3 or not all(parts):  # vendor/model/effort
            raise ValueError(f"unreadable LLM fallback {text!r}")
        found.append((parts[0], parts[1], parts[2]))
    return tuple(found)


def build_role_chain(
    settings: DeliberatorSettings,
    environ: Mapping[str, str],
    first: LLMClient,
    *,
    build: Callable[..., LLMClient] = build_llm,
) -> ModelChain:
    """Put the role's chosen client first, then one client per handed-over fallback."""
    model = settings.model_for_role(settings.peer_role or "judge")
    label = f"{settings.llm_provider}/{model}/{settings.effort}"
    candidates = [RoleCandidate(label, model, first)]
    for vendor, fallback_model, effort in handed_fallbacks(settings):
        client = build(
            vendor,
            api_key=environ.get(key_env_var(vendor)),
            model=fallback_model,
            max_tokens=settings.max_tokens,
            effort=effort,
        )
        candidates.append(
            RoleCandidate(f"{vendor}/{fallback_model}/{effort}", fallback_model, client)
        )
    return ModelChain(candidates)
