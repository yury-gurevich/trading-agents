"""Forecaster settings and justified tunables.

Agent: forecaster
Role: own the forecaster's model identity and advisory scoring policy defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ForecasterSettings(AgentSettings):
    """Settings for the advisory FinBERT sentiment forecaster."""

    model_config = SettingsConfigDict(
        env_prefix="FORECASTER_", frozen=True, protected_namespaces=()
    )

    model_id: str = "finbert-sentiment"
    model_ref: str = "ProsusAI/finbert"
    news_lookback_days: int = tunable(
        7,
        why="Recent-headline window scored for a subject's shadow sentiment.",
        ge=1,
        le=90,
        unit="days",
    )
    headlines_for_full_confidence: int = tunable(
        5,
        why="Headline count at which the advisory reading reaches full confidence.",
        ge=1,
        le=50,
        unit="headlines",
    )
