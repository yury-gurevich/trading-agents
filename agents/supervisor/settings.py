"""Supervisor settings and justified fault-lineage tunables.

Agent: supervisor
Role: own supervisor audit-record limits without routing or trading logic.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class SupervisorSettings(AgentSettings):
    """Settings for supervisor message and fault graph writes."""

    model_config = SettingsConfigDict(env_prefix="SUPERVISOR_", frozen=True)

    max_fault_message_chars: int = tunable(
        500,
        why=(
            "Fault nodes should stay scannable in graph views while keeping enough "
            "error text for operator triage."
        ),
        ge=80,
        le=2000,
        unit="chars",
    )
