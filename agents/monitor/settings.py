"""Monitor settings and justified exit-rule tunables.

Agent: monitor
Role: own monitor policy defaults for paper-stage position checks.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class MonitorSettings(AgentSettings):
    """Settings for deterministic monitor checks."""

    model_config = SettingsConfigDict(env_prefix="MONITOR_", frozen=True)

    default_horizon_days: int = tunable(
        14,
        why="Paper-stage holding window when no analyst horizon exists in the graph.",
        ge=0,
        le=365,
        unit="days",
    )
    price_lookback_days: int = tunable(
        2,
        why="Small rolling window to get the latest close across non-trading days.",
        ge=0,
        le=14,
        unit="days",
    )
    default_stop_pct: float = tunable(
        0.05,
        why="Fallback stop policy if OrderIntent lineage is missing stop_pct.",
        ge=0.0,
        le=1.0,
    )
    default_target_pct: float = tunable(
        0.10,
        why="Fallback target policy if OrderIntent lineage is missing target_pct.",
        ge=0.0,
        le=1.0,
    )
