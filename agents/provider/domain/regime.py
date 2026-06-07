"""Market-regime classification for provider outputs.

Agent: provider
Role: classify deterministic regime labels and policy inputs from raw source data.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.provider.settings import ProviderSettings
    from agents.provider.sources import RegimeInputs
    from contracts.common import RegimeLabel


def classify_regime(inputs: RegimeInputs, settings: ProviderSettings) -> RegimeLabel:
    """Map VIX inputs to the contract's regime labels."""
    if inputs.vix is None:
        return "neutral"
    if inputs.vix >= settings.vix_extreme_threshold:
        return "extreme_volatility"
    if inputs.vix >= settings.vix_high_threshold:
        return "high_volatility"
    if inputs.vix >= settings.vix_risk_off_threshold:
        return "risk_off"
    if inputs.vix <= settings.vix_risk_on_threshold:
        return "risk_on"
    return "neutral"
