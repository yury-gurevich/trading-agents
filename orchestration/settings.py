"""Orchestration settings and justified paper-loop tunables.

Agent: orchestration
Role: own dispatcher defaults while keeping provider and broker ports injectable.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class OrchestratorSettings(AgentSettings):
    """Settings for the paper-stage daily dispatcher."""

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_", frozen=True)

    universe: str = tunable(
        "sp500",
        why="Paper-stage default scan universe when a trigger does not specify one.",
    )
    provider_max_staleness_days: int = tunable(
        7,
        why="Daily dispatcher accepts a one-week fixture window across weekends.",
        ge=0,
        le=30,
        unit="days",
    )
    pm_starting_cash: Decimal = tunable(
        Decimal("100000.00"),
        why="Seed paper PM sizing with a deterministic portfolio value.",
        ge=0.0,
        le=1000000000.0,
        unit="USD",
    )
