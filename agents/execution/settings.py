"""Execution settings and justified paper-stage tunables.

Agent: execution
Role: own execution-stage configuration without leaking broker secrets.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable

ExecutionStageValue = Literal["paper", "broker_shadow", "live_manual", "live_autopilot"]
OrderPriceToleranceMode = Literal["flat", "scaled"]


class ExecutionSettings(AgentSettings):
    """Settings for the paper-stage execution agent."""

    model_config = SettingsConfigDict(
        env_prefix="EXECUTION_", frozen=True, populate_by_name=True
    )

    stage: ExecutionStageValue = "paper"
    slippage_bps: int = tunable(
        0,
        why=(
            "Paper fills default to the submitted reference price for "
            "deterministic tests."
        ),
        ge=0,
        le=1000,
        unit="bps",
    )
    order_price_tolerance_bps: int = tunable(
        50,
        why=(
            "Bound entry and discretionary-exit orders near the PM's decided "
            "price so after-close decisions do not trade at unevaluated opens."
        ),
        ge=0,
        le=500,
        unit="bps",
    )
    order_price_tolerance_mode: OrderPriceToleranceMode = "flat"
    scaled_order_price_tolerance_atr_multiplier: float = tunable(
        0.50,
        why=(
            "Measure a challenger band near half of decision-time daily ATR; "
            "overnight gaps observed for S149 cluster around 0.3-0.6x ATR."
        ),
        ge=0.0,
        le=2.0,
        unit="ratio",
    )
    scaled_order_price_tolerance_floor_bps: int = tunable(
        25,
        why=(
            "Keep the volatility-scaled challenger from becoming so narrow "
            "that quiet names cannot trade at all."
        ),
        ge=0,
        le=500,
        unit="bps",
    )
    scaled_order_price_tolerance_ceiling_bps: int = tunable(
        250,
        why=(
            "Keep the volatility-scaled challenger narrow enough that "
            "ADR-0018 still rejects materially unevaluated opens."
        ),
        ge=0,
        le=500,
        unit="bps",
    )
    min_promotion_runs: int = tunable(
        10,
        why="Require ten completed runs before stage promotion.",
        ge=3,
        le=200,
        unit="runs",
    )
    min_approval_rate: float = tunable(
        0.70,
        why="Minimum approval-rate evidence before stage promotion.",
        ge=0.0,
        le=1.0,
    )
    # Alpaca paper broker (ADR-0006). Aliases bridge the unprefixed .env names;
    # the paper-specific key wins so live keys are never picked up by accident.
    alpaca_api_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias=AliasChoices(
            "EXECUTION_ALPACA_API_KEY", "ALPACA_PAPER_API_KEY", "ALPACA_API_KEY"
        ),
    )
    alpaca_secret_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias=AliasChoices(
            "EXECUTION_ALPACA_SECRET_KEY",
            "ALPACA_PAPER_API_SECRET",
            "ALPACA_API_SECRET",
        ),
    )
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        validation_alias=AliasChoices("EXECUTION_ALPACA_BASE_URL", "ALPACA_BASE_URL"),
    )
    alpaca_timeout: int = tunable(
        15,
        why="Bound the Alpaca REST call so a slow broker cannot hang the run.",
        ge=1,
        le=60,
        unit="seconds",
    )
    deliberation_grace_seconds: int = tunable(
        default=900,
        ge=0,
        le=3600,
        why=(
            "How long a BUY-carrying PMRun waits for its DeliberationRun before "
            "submitting anyway. 0 restores the pre-DL-98 race. Exits never wait "
            "(S147 / ADR-0017): a sell-only run ignores this entirely."
        ),
    )
    broker_stop_fallback_stop_pct: float = tunable(
        0.05,
        why=(
            "Protect broker-adopted positions that lack PM stop lineage with the "
            "same paper-stage downside floor used by monitor reconciliation."
        ),
        gt=0.0,
        le=1.0,
        unit="fraction",
    )

    @model_validator(mode="after")
    def _scaled_tolerance_bounds_are_ordered(self) -> ExecutionSettings:
        if (
            self.scaled_order_price_tolerance_floor_bps
            > self.scaled_order_price_tolerance_ceiling_bps
        ):
            raise ValueError("scaled tolerance floor must be <= ceiling")
        return self
