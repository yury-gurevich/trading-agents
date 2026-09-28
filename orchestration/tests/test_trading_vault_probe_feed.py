"""Trading vault probe feed tests.

Agent: orchestration
Role: verify the seeder's alpaca-data probe builds its source on the feed the
fleet reads: the provider's own default, unless the env names one.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.provider.settings_feeds import ProviderFeedSettings
from orchestration.packs import trading_vault_probes as probes

if TYPE_CHECKING:
    import pytest

_KEYS = {"PROVIDER_ALPACA_API_KEY": "x", "PROVIDER_ALPACA_API_SECRET": "y"}


def test_alpaca_data_probe_tests_the_fleets_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PROV-OUT-07: the probe asks for SIP by default because the provider does;
    the default is read from the provider, and the env override still wins."""
    assert probes._alpaca_data_source(_KEYS)._feed == "sip"
    override = {**_KEYS, "PROVIDER_ALPACA_DATA_FEED": "iex"}
    assert probes._alpaca_data_source(override)._feed == "iex"
    field = ProviderFeedSettings.model_fields["alpaca_data_feed"]
    monkeypatch.setattr(field, "default", "provider-default")
    assert probes._alpaca_data_source(_KEYS)._feed == "provider-default"
