"""Shadow-book settings and justified forward-return horizons.

Agent: orchestration
Role: own the read-only shadow-book derivation defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ShadowBookSettings(AgentSettings):
    """Configuration for the recommendation outcome scorecard."""

    model_config = SettingsConfigDict(env_prefix="SHADOW_BOOK_", frozen=True)

    short_horizon_days: int = tunable(
        1,
        why="First subsequent trading-day return for immediate selection feedback.",
        ge=1,
        le=20,
        unit="trading days",
    )
    medium_horizon_days: int = tunable(
        5,
        why="One trading-week return for short-horizon selection quality.",
        ge=1,
        le=60,
        unit="trading days",
    )
    long_horizon_days: int = tunable(
        20,
        why="One trading-month return aligned with the existing return-model horizon.",
        ge=1,
        le=120,
        unit="trading days",
    )
    confidence_bucket_width: float = tunable(
        0.05,
        why="Five-point confidence bands keep the small scorecard samples inspectable.",
        gt=0.0,
        le=1.0,
        unit="confidence",
    )

    @property
    def horizons(self) -> tuple[int, ...]:
        """Return configured horizons once each, shortest first."""
        return tuple(
            sorted(
                {
                    self.short_horizon_days,
                    self.medium_horizon_days,
                    self.long_horizon_days,
                }
            )
        )
