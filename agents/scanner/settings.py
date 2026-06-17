"""Scanner agent settings and justified filter tunables.

Agent: scanner
Role: own scanner-specific universe, lookback, filter, and ranking defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ScannerSettings(AgentSettings):
    """Settings for the universe-reduction scanner agent."""

    model_config = SettingsConfigDict(env_prefix="SCANNER_", frozen=True)

    lookback_days: int = tunable(
        5,
        why="Short deterministic first-slice window; broader scans tune this later.",
        ge=2,
        le=252,
        unit="days",
    )
    min_relative_strength: float = tunable(
        0.02,
        why="Require a positive lookback return before deeper analyst work.",
        ge=-1.0,
        le=5.0,
    )
    min_price: float = tunable(
        5.0,
        why="Avoid illiquid penny-price names in the first scanner slice.",
        ge=0.01,
        le=1000.0,
        unit="USD",
    )
    min_average_volume: float = tunable(
        500_000.0,
        why="Require enough daily liquidity for later sizing and execution checks.",
        ge=0.0,
        le=1_000_000_000.0,
        unit="shares",
    )
    candidate_cap: int = tunable(
        5,
        why="Keep the first vertical slice small and explainable for analyst handoff.",
        ge=1,
        le=50,
    )
    benchmark_ticker: str = "SPY"
    max_beta: float = tunable(
        2.5,
        why="Exclude names whose systematic risk (beta vs the benchmark) is too high.",
        ge=0.0,
        le=10.0,
    )
    beta_min_observations: int = tunable(
        3,
        why="Minimum aligned daily returns before the beta-cap is trusted to gate.",
        ge=2,
        le=252,
        unit="observations",
    )
