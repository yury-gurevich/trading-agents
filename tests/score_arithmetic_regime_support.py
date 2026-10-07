"""Provider RPC fixtures with explicit classification settings.

Agent: testing
Role: fetch regimes through an in-process bus and deterministic fake source.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import RegimeContext
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus


def provider_settings(moved: bool = False) -> ProviderSettings:
    """Provide both default and changed thresholds and policy constants."""
    if not moved:
        return ProviderSettings()
    return ProviderSettings(
        vix_risk_on_threshold=12.0,
        vix_risk_off_threshold=22.0,
        vix_high_threshold=28.0,
        vix_extreme_threshold=40.0,
        base_min_confidence=0.51,
        base_stop_loss_pct=0.07,
        base_take_profit_pct=0.13,
        base_max_holding_days=12,
    )


def regime_for(vix: float | None, config: ProviderSettings) -> RegimeContext:
    """Read the actual provider response without credentials or external data."""
    bus = InProcessBus()
    ProviderAgent(
        bus,
        graph=InMemoryGraphStore(),
        source=FakeDataSource(vix=vix),
        settings=config,
    ).bind()
    response = bus.request(
        AgentMessage(
            sender="analyst",
            recipient="provider",
            message_type="request",
            capability="get_regime",
            payload={"as_of": date(2026, 10, 5)},
        )
    )
    assert response.message_type == "response"
    return RegimeContext.model_validate(response.payload)
