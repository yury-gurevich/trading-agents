"""The agent's EHLO resend envelope — how long and how often to ask master.

Agent: kernel
Role: declare the bounded tunables every agent's bootstrap reads when it resends
      EHLO to a sleeping or busy master (DL-249 D1); no env key needs setting.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from kernel.config import AgentSettings, tunable


class EhloSettings(AgentSettings):
    """Resend budget for one agent boot's EHLO (``MST-TRG-01``, ``MST-FAIL-06``)."""

    ehlo_attempt_timeout_seconds: float = tunable(
        30.0,
        why=(
            "Seconds one EHLO attempt waits for ACTIVATE; today's single-attempt "
            "value, so no attempt is shorter than before (master cold start ~21 s "
            "plus a 2-6 s activation, DL-248)."
        ),
        ge=5.0,
        le=120.0,
        unit="seconds",
    )
    ehlo_max_attempts: int = tunable(
        6,
        why=(
            "EHLO sends per boot before the agent exits; bounds master's load when "
            "a refused connection fails instantly (DL-249 D1)."
        ),
        ge=1,
        le=20,
    )
    ehlo_budget_seconds: float = tunable(
        300.0,
        why=(
            "Total seconds one boot may spend activating; must not exceed master's "
            "replay window (handshake_timeout_2_seconds), so every resend is replayed."
        ),
        ge=30.0,
        le=600.0,
        unit="seconds",
    )
    ehlo_backoff_base_seconds: float = tunable(
        1.0,
        why="First backoff ceiling; doubles per failed attempt, full jitter below it.",
        ge=0.1,
        le=10.0,
        unit="seconds",
    )
    ehlo_backoff_cap_seconds: float = tunable(
        30.0,
        why="Largest backoff ceiling, so a late attempt still lands inside the budget.",
        ge=1.0,
        le=120.0,
        unit="seconds",
    )
