"""Provider agent settings and justified policy tunables.

Agent: provider
Role: own provider-specific policy defaults, integrity thresholds, and secrets.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from agents.provider.settings_feeds import ProviderFeedSettings
from kernel import tunable


class ProviderSettings(ProviderFeedSettings):
    """Settings for the market-data boundary agent."""

    base_min_confidence: float = tunable(
        0.60,
        why="Default downstream confidence floor from the reference policy.",
        ge=0.0,
        le=1.0,
    )
    base_stop_loss_pct: float = tunable(
        0.05,
        why="Reference protective stop; bounded below the PRD maximum risk cap.",
        ge=0.0,
        le=0.08,
    )
    base_take_profit_pct: float = tunable(
        0.10,
        why="Reference reward target paired with the default stop-loss policy.",
        ge=0.01,
        le=1.0,
    )
    base_max_holding_days: int = tunable(
        10,
        why="Short tactical holding window used until agent scorecards tune it.",
        ge=1,
        le=60,
        unit="days",
    )
    max_daily_move_sigma: float = tunable(
        8.0,
        why="Extreme daily-return guard; 8 sigma not 4.0 (legit movers, DRIFT-012).",
        ge=0.1,
        le=20.0,
        unit="sigma",
    )
    max_staleness_days: int = tunable(
        3,
        why=(
            "Market data older than three TRADING SESSIONS is called out as stale; "
            "the count excludes weekends + NYSE holidays (DL-10), not calendar days."
        ),
        ge=0,
        le=30,
        unit="sessions",
    )
    vix_risk_on_threshold: float = tunable(
        15.0,
        why="Low-volatility VIX level where risk-on defaults may apply.",
        ge=0.0,
        le=100.0,
    )
    vix_risk_off_threshold: float = tunable(
        20.0,
        why="Elevated VIX level where new-risk posture should tighten.",
        ge=0.0,
        le=100.0,
    )
    vix_high_threshold: float = tunable(
        25.0,
        why="High-volatility VIX level from the reference regime gate.",
        ge=0.0,
        le=100.0,
    )
    vix_extreme_threshold: float = tunable(
        35.0,
        why="Extreme-volatility VIX level from the reference regime gate.",
        ge=0.0,
        le=150.0,
    )
