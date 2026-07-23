"""Execution settings and justified paper-stage tunables.

Agent: execution
Role: own execution-stage configuration without leaking broker secrets.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable

ExecutionStageValue = Literal["paper", "broker_shadow", "live_manual", "live_autopilot"]


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
