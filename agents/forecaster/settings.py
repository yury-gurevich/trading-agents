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

    # ── LightGBM price/return shadow signal (qlib Phase Q1) ──────────────────
    return_model_id: str = "lgbm-return-v1"
    return_model_ref: str = "lightgbm-gbdt"
    return_model_path: str = "models/lgbm-return-v1.txt"
    price_lookback_days: int = tunable(
        90,
        why="Trailing calendar window of daily bars fetched to build price features.",
        ge=30,
        le=365,
        unit="days",
    )
    return_short_horizon: int = tunable(
        1,
        why="Short trailing-return horizon in the price feature row.",
        ge=1,
        le=10,
        unit="days",
    )
    return_mid_horizon: int = tunable(
        5,
        why="Medium trailing-return horizon in the price feature row.",
        ge=2,
        le=30,
        unit="days",
    )
    return_long_horizon: int = tunable(
        20,
        why="Long trailing-return horizon in the price feature row.",
        ge=5,
        le=120,
        unit="days",
    )
    volatility_window: int = tunable(
        20,
        why="Window for realized volatility of daily returns.",
        ge=2,
        le=120,
        unit="days",
    )
    momentum_window: int = tunable(
        20,
        why="Window for the price/SMA momentum and the volume ratio.",
        ge=2,
        le=120,
        unit="days",
    )
    bars_for_full_confidence: int = tunable(
        60,
        why="Bar count at which the price reading reaches full confidence.",
        ge=1,
        le=365,
        unit="bars",
    )
    return_squash_scale: float = tunable(
        0.05,
        why="Logistic scale mapping a predicted return onto the 0-1 value.",
        ge=0.001,
        le=1.0,
        unit="return",
    )
    retrain_window_days: int = tunable(
        60,
        why="Trailing distinct-date evaluation window for the rolling IC-decay check.",
        ge=20,
        le=252,
        unit="trading days",
    )
    retrain_trigger_fraction: float = tunable(
        0.5,
        why="Fraction of the reference metric below which a retrain is recommended.",
        gt=0.0,
        le=1.0,
    )
    retrain_horizon_days: int = tunable(
        20,
        why=(
            "Forward-return horizon the decay trigger and champion comparison score "
            "at — S110 baseline is strongest at h=20 (IC-IR 0.27)."
        ),
        ge=1,
        le=60,
        unit="days",
    )
    retrain_min_cases: int = tunable(
        500,
        why=(
            "Minimum aligned recent-window observations before a decay verdict "
            "is meaningful."
        ),
        ge=50,
    )

    # ── LLM champion slot (ADR-0010) ─────────────────────────────────────────
    system_prompt: str = tunable(
        "",
        why=(
            "Champion slot for the DSPy-compiled macro-event extraction prompt "
            "(ADR-0010). Pre-declared for P13; empty until the LLM path ships."
        ),
    )
