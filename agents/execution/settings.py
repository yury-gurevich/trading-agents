"""Execution settings and justified paper-stage tunables.

Agent: execution
Role: own execution-stage configuration without leaking broker secrets.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable

ExecutionStageValue = Literal["paper", "broker_shadow", "live_manual", "live_autopilot"]


class ExecutionSettings(AgentSettings):
    """Settings for the paper-stage execution agent."""

    model_config = SettingsConfigDict(env_prefix="EXECUTION_", frozen=True)

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
    close_quantity: int = tunable(
        1,
        why=(
            "CloseDecision names a position but not its quantity until monitor owns "
            "position state; use one whole-share close fixtures for this slice."
        ),
        ge=1,
        le=1000000,
        unit="shares",
    )
    close_reference_price: Decimal = tunable(
        Decimal("1.00"),
        why=(
            "execute_close is fixture-driven before monitor supplies prices; this "
            "keeps the broker path exercised without external data."
        ),
        ge=0.01,
        le=1000000.0,
        unit="USD",
    )
    alpaca_api_key: str | None = Field(default=None, repr=False)
    alpaca_secret_key: str | None = Field(default=None, repr=False)
