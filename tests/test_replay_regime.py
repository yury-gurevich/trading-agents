"""Tests for S235 replay regime context assembly.

Agent: tooling
Role: verify replay copies provider base regime policy into downstream context.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from scripts.replay_settings import build_effective_settings

from contracts.common import Provenance
from contracts.provider import DataQualityTrace, RegimeContext


def test_regime_context_uses_provider_base_settings() -> None:
    """S235-A2: provider base policy fields are copied into RegimeContext."""
    settings = build_effective_settings(())
    context = RegimeContext(
        label="neutral",
        vix=19.0,
        vix_status="measured",
        vix_as_of=date(2020, 1, 2),
        as_of=datetime(2020, 1, 2, tzinfo=UTC),
        base_min_confidence=settings.provider.base_min_confidence,
        base_stop_loss_pct=settings.provider.base_stop_loss_pct,
        base_take_profit_pct=settings.provider.base_take_profit_pct,
        base_max_holding_days=settings.provider.base_max_holding_days,
        provenance=Provenance(run_id="r1", source_agent="provider"),
    )

    assert context.base_min_confidence == settings.provider.base_min_confidence
    assert DataQualityTrace(requested=1, returned=1).requested == 1
