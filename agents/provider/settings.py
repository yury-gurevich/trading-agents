"""Provider agent settings and justified policy tunables.

Agent: provider
Role: own provider-specific policy defaults, integrity thresholds, and secrets.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ProviderSettings(AgentSettings):
    """Settings for the market-data boundary agent."""

    model_config = SettingsConfigDict(env_prefix="PROVIDER_", frozen=True)

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
        4.0,
        why="Flag daily returns that are extreme relative to the requested window.",
        ge=0.1,
        le=20.0,
        unit="sigma",
    )
    max_staleness_days: int = tunable(
        3,
        why="Market data older than three sessions should be called out as stale.",
        ge=0,
        le=30,
        unit="days",
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

    finnhub_timeout: int = tunable(
        10,
        why="Bound the Finnhub fundamentals HTTPS call so a slow feed cannot hang.",
        ge=1,
        le=60,
        unit="seconds",
    )

    finnhub_base_url: str = Field(default="https://finnhub.io/api/v1")
    finnhub_api_key: str = Field(default="", repr=False)
    fred_api_key: str = Field(default="", repr=False)

    # FMP — validation sub-universe / failover feed (~87 symbols, ADR-0006).
    fmp_base_url: str = Field(default="https://financialmodelingprep.com")
    fmp_api_key: str = Field(default="", repr=False)
    fmp_timeout: int = tunable(
        15,
        why="Bound the FMP EOD HTTPS call so a slow feed cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )

    # Tiingo — primary full-universe live OHLCV feed (ADR-0006; closes DRIFT-009).
    tiingo_base_url: str = Field(default="https://api.tiingo.com")
    tiingo_api_key: str = Field(default="", repr=False)
    tiingo_timeout: int = tunable(
        15,
        why="Bound the Tiingo EOD HTTPS call so a slow feed cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )

    # Alpha Vantage — vendor news sentiment (provider-sentiment challenger, ADR-0002).
    alphavantage_base_url: str = Field(default="https://www.alphavantage.co")
    alphavantage_api_key: str = Field(default="", repr=False)
    alphavantage_timeout: int = tunable(
        25,
        why="Bound the Alpha Vantage sentiment call so a slow feed cannot hang.",
        ge=1,
        le=60,
        unit="seconds",
    )
    finnhub_news_lookback_days: int = tunable(
        7,
        why=(
            "Trailing window of company news to fetch; recent headlines only,"
            " not the full OHLCV lookback."
        ),
        ge=1,
        le=90,
        unit="days",
    )
    max_news_per_ticker: int = tunable(
        20,
        why=(
            "Cap headlines per ticker so a noisy feed cannot dominate"
            " the downstream sentiment pillar."
        ),
        ge=1,
        le=100,
    )
    finnhub_earnings_lookahead_days: int = tunable(
        30,
        why=(
            "Forward window scanned for each ticker's next earnings date;"
            " comfortably covers any scanner earnings-exclusion threshold."
        ),
        ge=1,
        le=180,
        unit="days",
    )
