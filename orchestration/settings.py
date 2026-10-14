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
    container_sensor_first_read_hours: int = tunable(
        24,
        why=(
            "The sensor's first read covers one day, so the day's deploys before it "
            "are seen and a month of old events does not arrive as one alarm (DL-301)."
        ),
        ge=1,
        le=168,
        unit="hours",
    )
    container_sensor_max_lookback_hours: int = tunable(
        168,
        why=(
            "A read after a long gap covers at most a week; the workspace keeps 30 "
            "days, and anything older than a week is history, not an alarm (DL-301)."
        ),
        ge=24,
        le=720,
        unit="hours",
    )
    container_sensor_overlap_minutes: int = tunable(
        10,
        why=(
            "An event reached the workspace up to 2 min 36 s after it happened "
            "(measured 2026-10-14, 48 hours); each read starts this long before the "
            "last one ended, and a row read twice is recorded once (DL-301)."
        ),
        ge=3,
        le=60,
        unit="minutes",
    )
    container_sensor_alarm_groups_max: int = tunable(
        8,
        why=(
            "One alarm message names at most this many kinds of failure and "
            "counts the rest, so it stays readable and inside Telegram's limit."
        ),
        ge=1,
        le=20,
    )
    container_sensor_timeout_seconds: float = tunable(
        20.0,
        why=(
            "Each workspace call is bounded so a slow read cannot hold the fire; a "
            "read of one day to one week took 1.3 to 3.6 s (measured 2026-10-14)."
        ),
        ge=1.0,
        le=120.0,
        unit="seconds",
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
