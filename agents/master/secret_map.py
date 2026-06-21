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

# (kv_secret_name, env_var_name) pairs per agent type.
# kv_secret_name: kebab-case name as stored in Key Vault.
# env_var_name: the exact os.environ key the agent's settings will read;
#   must match field + env_prefix from each agent's Settings class.
# Only agents with external API credentials appear; all others receive no secrets.
AGENT_SECRETS: dict[str, list[tuple[str, str]]] = {
    "provider": [
        ("tiingo-api-key", "PROVIDER_TIINGO_API_KEY"),
        ("finnhub-api-key", "PROVIDER_FINNHUB_API_KEY"),
        ("fmp-api-key", "PROVIDER_FMP_API_KEY"),
        ("alpaca-key-id", "PROVIDER_ALPACA_API_KEY"),
        ("alpaca-secret-key", "PROVIDER_ALPACA_SECRET_KEY"),
    ],
    "execution": [
        ("alpaca-key-id", "EXECUTION_ALPACA_API_KEY"),
        ("alpaca-secret-key", "EXECUTION_ALPACA_SECRET_KEY"),
    ],
    "operator": [
        # Anthropic SDK reads ANTHROPIC_API_KEY directly — no prefix.
        ("anthropic-api-key", "ANTHROPIC_API_KEY"),
    ],
}


def resolve_config(agent_type: str, store: SecretStore) -> dict[str, object]:
    """Fetch entitled secrets for *agent_type*; omit missing (empty-string) values.

    Returns a flat dict keyed by the canonical env-var names agents' settings read,
    ready to be written into os.environ by kernel.bootstrap._apply_config().
    """
    config: dict[str, object] = {}
    for kv_name, env_name in AGENT_SECRETS.get(agent_type, []):
        value = store.get_secret(kv_name)
        if value:
            config[env_name] = value
    return config
