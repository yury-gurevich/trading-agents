"""Provider feed and network settings.

Agent: provider
Role: own provider feed credentials, pacing, request bounds, and source URLs.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ProviderFeedSettings(AgentSettings):
    """Settings for provider-owned external feed adapters."""

    model_config = SettingsConfigDict(env_prefix="PROVIDER_", frozen=True)

    finnhub_timeout: int = tunable(
        10,
        why="Bound the Finnhub fundamentals HTTPS call so a slow feed cannot hang.",
        ge=1,
        le=60,
        unit="seconds",
    )
    finnhub_request_budget_per_minute: int = tunable(
        55,
        why="Pace per-ticker Finnhub calls just under the 60 req/min free-tier cap.",
        ge=0,
        le=600,
        unit="requests/minute",
    )
    finnhub_degraded_note_ticker_cap: int = tunable(
        5,
        why=(
            "Bound attributed feed-degradation notes while naming representative "
            "tickers."
        ),
        ge=1,
        le=50,
    )

    ingest_chunk_size: int = tunable(
        0,
        why=(
            "Universe sub-batch size for paced ingest; 0 disables chunking (one"
            " single-shot batch). Tune against the per-ticker feed's per-minute cap."
        ),
        ge=0,
        le=500,
    )
    ingest_chunk_delay_seconds: float = tunable(
        60.0,
        why=(
            "Pause between ingest chunks so the aggregate per-minute API call rate"
            " stays under the free-tier ceiling (Finnhub ~60/min, 4 calls/ticker)."
        ),
        ge=0.0,
        le=600.0,
        unit="seconds",
    )
    ingest_ohlcv_only: bool = Field(default=False)  # OHLCV-only fast mode (DL-29)

    finnhub_base_url: str = Field(default="https://finnhub.io/api/v1")
    finnhub_api_key: str = Field(default="", repr=False)
    fred_api_key: str = Field(default="", repr=False)

    fmp_base_url: str = Field(default="https://financialmodelingprep.com")
    fmp_api_key: str = Field(default="", repr=False)
    fmp_timeout: int = tunable(
        15,
        why="Bound the FMP EOD HTTPS call so a slow feed cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )

    tiingo_base_url: str = Field(default="https://api.tiingo.com")
    tiingo_api_key: str = Field(default="", repr=False)
    tiingo_timeout: int = tunable(
        15,
        why="Bound the Tiingo EOD HTTPS call so a slow feed cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )

    alpaca_data_base_url: str = Field(default="https://data.alpaca.markets")
    alpaca_api_key: str = Field(default="", repr=False)
    alpaca_api_secret: str = Field(default="", repr=False)
    alpaca_data_feed: str = Field(default="iex")
    alpaca_data_timeout: int = tunable(
        15,
        why="Bound the Alpaca bars HTTPS call so a slow feed cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )

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
        why="Trailing window of company news to fetch; recent headlines only.",
        ge=1,
        le=90,
        unit="days",
    )
    max_news_per_ticker: int = tunable(
        20,
        why="Cap headlines per ticker so a noisy feed cannot dominate sentiment.",
        ge=1,
        le=100,
    )
    finnhub_earnings_lookahead_days: int = tunable(
        30,
        why="Forward window scanned for each ticker's next earnings date.",
        ge=1,
        le=180,
        unit="days",
    )
