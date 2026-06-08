"""Analyst agent settings and justified scoring tunables.

Agent: analyst
Role: own analyst lookback, indicator, and confidence-model defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class AnalystSettings(AgentSettings):
    """Settings for deterministic analyst scoring."""

    model_config = SettingsConfigDict(env_prefix="ANALYST_", frozen=True)

    lookback_days: int = tunable(
        7,
        why="Use a short technical window for the first end-to-end P2 slice.",
        ge=2,
        le=252,
        unit="days",
    )
    min_history_bars: int = tunable(
        2,
        why="At least two closes are required to compute lookback momentum.",
        ge=2,
        le=60,
        unit="bars",
    )
    short_ma_bars: int = tunable(
        2,
        why="Tiny short moving average keeps the first-slice signal responsive.",
        ge=1,
        le=60,
        unit="bars",
    )
    long_ma_bars: int = tunable(
        5,
        why="Small long moving average gives trend context without broad history.",
        ge=2,
        le=120,
        unit="bars",
    )
    candidate_score_weight: float = tunable(
        0.45,
        why="Scanner rank is trusted as the primary first-slice prior.",
        ge=0.0,
        le=1.0,
    )
    momentum_weight: float = tunable(
        0.35,
        why="Recent price momentum is the main analyst-owned technical signal.",
        ge=0.0,
        le=1.0,
    )
    trend_weight: float = tunable(
        0.20,
        why="Moving-average trend is a stabilizer, not the dominant signal.",
        ge=0.0,
        le=1.0,
    )
    score_scale: float = tunable(
        0.20,
        why="A twenty-percent lookback move maps to a full technical component.",
        ge=0.01,
        le=5.0,
    )
    trend_scale: float = tunable(
        0.10,
        why="A ten-percent short-vs-long MA spread maps to a full trend component.",
        ge=0.01,
        le=5.0,
    )
    confidence_floor: float = tunable(
        0.30,
        why="Keep weak but valid technical evidence below the provider regime gate.",
        ge=0.0,
        le=1.0,
    )
    confidence_span: float = tunable(
        0.60,
        why="Let strong technical evidence clear the default 0.60 regime threshold.",
        ge=0.0,
        le=1.0,
    )
