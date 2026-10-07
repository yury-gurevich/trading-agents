"""Record the settings used to select a provider regime label.

Agent: provider
Role: make the four classification thresholds durable on the regime context.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import VixThresholds

if TYPE_CHECKING:
    from agents.provider.settings import ProviderSettings


def record_thresholds(settings: ProviderSettings) -> VixThresholds:
    """Capture classification constants from this provider's active settings."""
    return VixThresholds(
        risk_on_at_or_below=settings.vix_risk_on_threshold,
        risk_off_from=settings.vix_risk_off_threshold,
        high_volatility_from=settings.vix_high_threshold,
        extreme_volatility_from=settings.vix_extreme_threshold,
    )
