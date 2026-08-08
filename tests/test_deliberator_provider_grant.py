"""The deliberator containers are granted a key for every provider they can select.

Agent: tooling
Role: bind the trading secret-map pack to the deliberator's provider factory, so
      `llm_provider` can never name a vendor whose key the fleet was never given.
External I/O: reads orchestration/packs/trading_secrets.json.

The deliberators start braindead: they never read `.env`, and master hands them
exactly what the secret map lists. So a provider the factory accepts but the pack
does not grant fails closed *only on the fleet* — it works on a laptop and raises
ConfigurationError in production. That gap is what this chore closed; this test is
what stops it reopening when a third vendor is added.
"""

from __future__ import annotations

import pytest

from agents.deliberator.llm_factory import KEY_ENV
from agents.master.tests.helpers import trading_secret_map

_DELIBERATORS = (
    "deliberator-manager",
    "deliberator-proponent",
    "deliberator-opponent",
)


@pytest.mark.parametrize("agent_type", _DELIBERATORS)
@pytest.mark.parametrize("provider", sorted(KEY_ENV))
def test_every_selectable_provider_has_a_granted_key(
    agent_type: str, provider: str
) -> None:
    """Each deliberator role is entitled to the key env var build_llm will read."""
    granted = {env_name for _kv, env_name in trading_secret_map()[agent_type]}
    assert KEY_ENV[provider] in granted, (
        f"{agent_type} may select llm_provider={provider!r} but is not granted "
        f"{KEY_ENV[provider]} — it would raise ConfigurationError on the fleet"
    )
