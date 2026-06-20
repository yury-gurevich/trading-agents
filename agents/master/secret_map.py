"""Per-agent secret name registry.

Agent: master
Role: declare which Key Vault secret names each agent type is entitled to receive;
      resolve those secrets from a SecretStore into the ACTIVATE config payload.
External I/O: none (reads from injected SecretStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.master.key_vault import SecretStore

# Kebab-case Key Vault secret names per agent type.
# Only agents with external API credentials appear; all others receive no secrets.
AGENT_SECRETS: dict[str, list[str]] = {
    "provider": [
        "tiingo-api-key",
        "alpaca-key-id",
        "alpaca-secret-key",
        "finnhub-api-key",
        "fmp-api-key",
    ],
    "execution": [
        "alpaca-key-id",
        "alpaca-secret-key",
    ],
    "operator": [
        "anthropic-api-key",
    ],
}


def resolve_config(agent_type: str, store: SecretStore) -> dict[str, object]:
    """Fetch entitled secrets for *agent_type*; omit missing (empty-string) values.

    Returns a flat dict keyed by UPPER_SNAKE env-var names, ready for ACTIVATE config.
    """
    config: dict[str, object] = {}
    for name in AGENT_SECRETS.get(agent_type, []):
        value = store.get_secret(name)
        if value:
            config[name.upper().replace("-", "_")] = value
    return config
