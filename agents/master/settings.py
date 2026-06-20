"""Master bootstrap agent settings — handshake and fleet-management tunables.

Agent: master
Role: own master's lifecycle and handshake defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class MasterSettings(AgentSettings):
    """Settings for the master bootstrap lifecycle agent."""

    handshake_timeout_1_seconds: float = tunable(
        10.0,
        why="Seconds before master retries an unacknowledged ACTIVATE.",
        ge=1.0,
        le=60.0,
        unit="seconds",
    )
    handshake_max_retries: int = tunable(
        5,
        why="Maximum EHLO resend attempts before transitioning to INERT.",
        ge=1,
        le=20,
    )
    handshake_timeout_2_seconds: float = tunable(
        300.0,
        why="Total wait (seconds) before an unactivated agent transitions to INERT.",
        ge=30.0,
        le=600.0,
        unit="seconds",
    )

    model_config = SettingsConfigDict(env_prefix="MASTER_", frozen=True)
