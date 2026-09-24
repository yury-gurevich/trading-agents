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

    operator_timezone: str = tunable(
        "Australia/Melbourne",
        why="The operator reads their own local 24-hour time, never UTC (DL-216).",
    )

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
    preflight_max_age_minutes: int = tunable(
        70,
        why=(
            "Require the latest hourly fleet preflight with ten minutes of scheduling "
            "slack before placing a trading run."
        ),
        ge=10,
        le=240,
        unit="minutes",
    )


class DeliberationQualitySettings(AgentSettings):
    """Settings for the offline verdict-quality gate.

    Offline tooling: this is read by ``scripts/deliberation_quality.py`` and by
    nothing on the fleet, so it neither reaches a container nor owes a PARAM row.
    """

    model_config = SettingsConfigDict(env_prefix="DELIBERATION_QUALITY_", frozen=True)

    self_agreement_floor: float = tunable(
        0.56,
        why=(
            "The only self-agreement figure ever measured is DL-104's 9 of 16 = 56%, "
            "so the floor is set at the known-bad level: it cannot certify quality, "
            "but a further decline becomes visible. Deliberately uncalibrated until "
            "this sprint's own repeats exist, which is why the gate is warn-only."
        ),
        ge=0.0,
        le=1.0,
    )
    min_compared_pairs: int = tunable(
        10,
        why=(
            "Below ten comparable pairs the Wilson interval spans most of [0,1], so "
            "a floor comparison would be noise wearing a verdict's clothes."
        ),
        ge=1,
    )
