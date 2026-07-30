"""Analyst recommendation rationale text helpers.

Agent: analyst
Role: build deterministic recommendation summaries and evidence references.
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

ExitTrigger = Literal["stop", "thesis"]


def held_recommendation_context(
    ticker: str,
    confidence: float,
    exit_floor: float,
    exit_trigger: ExitTrigger | None,
) -> tuple[str, tuple[str, ...]]:
    """Return summary and evidence refs for a held-name recommendation."""
    if exit_trigger == "stop":
        return (
            f"{ticker} is already held; forced stop exit because "
            "the latest close is at or through the stop threshold.",
            ("contracts.stop_rule", "provider.market_data"),
        )
    if exit_trigger == "thesis":
        return (
            f"{ticker} is already held; thesis exit because confidence "
            f"{confidence:.3f} is below the conservative exit floor {exit_floor:.3f}.",
            (
                "analyst.technical_score",
                "provider.market_data",
                "provider.regime",
            ),
        )
    return (
        f"{ticker} is already held; analyst says hold because confidence "
        f"{confidence:.3f} is at or above the conservative exit floor "
        f"{exit_floor:.3f}.",
        (
            "analyst.technical_score",
            "provider.market_data",
            "provider.regime",
        ),
    )
