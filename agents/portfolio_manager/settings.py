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
        why="Seed the first PM slice with a paper portfolio before execution lands.",
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
