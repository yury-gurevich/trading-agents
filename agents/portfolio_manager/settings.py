"""Portfolio Manager settings and justified risk tunables.

Agent: portfolio_manager
Role: own portfolio sizing and risk-policy defaults for order decisions.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class PortfolioManagerSettings(AgentSettings):
    """Settings for deterministic portfolio sizing and risk checks."""

    model_config = SettingsConfigDict(env_prefix="PORTFOLIO_MANAGER_", frozen=True)

    starting_cash: Decimal = tunable(
        Decimal("100000.00"),
        why=(
            "Bootstrap a genuinely fresh paper graph before any execution account "
            "snapshot exists; normal sizing uses execution-recorded account equity."
        ),
        ge=0.0,
        le=1000000000.0,
        unit="USD",
    )
    max_position_pct: Decimal = tunable(
        Decimal("0.10"),
        why="Cap one new order at ten percent of portfolio value for first-slice risk.",
        ge=0.0,
        le=1.0,
    )
    max_positions: int = tunable(
        10,
        why="Keep portfolio concentration bounded before sector caps exist.",
        ge=1,
        le=500,
        unit="positions",
    )
    cash_buffer_pct: Decimal = tunable(
        Decimal("0.05"),
        why="Hold back cash so sizing does not consume the full paper account.",
        ge=0.0,
        le=0.95,
    )
    min_order_quantity: int = tunable(
        1,
        why="Execution receives whole-share order intents in this slice.",
        ge=1,
        le=1000000,
        unit="shares",
    )
    price_lookback_days: int = tunable(
        7,
        why=(
            "Ask provider for a short window so latest close survives non-trading days."
        ),
        ge=0,
        le=14,
        unit="days",
    )
    min_reward_risk_ratio: float = tunable(
        1.5,
        why=(
            "Reject setups whose reward-to-risk ratio (target_pct / stop_pct) is below "
            "the reference minimum; protects per-trade expectancy. 0 disables the gate."
        ),
        ge=0.0,
        le=10.0,
    )
    max_sector_pct: Decimal = tunable(
        Decimal("0.30"),
        why=(
            "Cap total deployment into any one sector as a fraction of portfolio value "
            "to bound concentration risk; 1.0 disables the gate."
        ),
        ge=0.0,
        le=1.0,
    )
    max_names_per_sector: int = tunable(
        3,
        why=(
            "Cap the NUMBER of issuers held in any one sector label; this is a "
            "label-bucket cap, while measured correlation is enforced separately."
        ),
        ge=0,
        le=500,
        unit="positions",
    )
    correlation_lookback_days: int = tunable(
        120,
        why=(
            "Bars used for pairwise return correlation; runs already carry this "
            "history, so the gate costs no market-data fetch."
        ),
        ge=20,
        le=250,
        unit="days",
    )
    correlation_threshold: float = tunable(
        0.70,
        why=(
            "Pairwise close-return correlation at or above which two issuers are "
            "treated as one correlated bet."
        ),
        ge=0.0,
        le=1.0,
    )
    max_correlated_cluster_pct: float = tunable(
        0.25,
        why=(
            "Cap one measured correlated issuer cluster as a fraction of portfolio "
            "value; tighter than sector labels because it measures the bet."
        ),
        ge=0.0,
        le=1.0,
    )
    min_correlation_bars: int = tunable(
        60,
        why=(
            "Minimum overlapping close-to-close returns for a usable pairwise "
            "correlation; below this the gate is not evaluated, never passed."
        ),
        ge=20,
        le=250,
        unit="bars",
    )
