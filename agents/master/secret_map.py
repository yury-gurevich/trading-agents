"""Per-agent secret entitlement resolution.

Agent: master
Role: resolve the Key Vault secrets each agent type is entitled to into the ACTIVATE
      config payload. The entitlement table is pack data (which types exist, which
      secrets they get) injected at boot — the substrate names no trading secret.
External I/O: reads the secret-map JSON file when load_secret_map is called; reads
      secret values from the injected SecretStore.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.master.key_vault import SecretStore

# Maps an agent type to its (kv_secret_name, env_var_name) entitlements.
#   kv_secret_name: kebab-case name as stored in Key Vault.
#   env_var_name: the exact os.environ key the agent's settings read (field + prefix).
# The trading content lives in a pack file (orchestration/packs/trading_secrets.json),
# loaded by path — never imported (ADR-0012, DL-12).
type SecretMap = Mapping[str, list[tuple[str, str]]]


def parse_secret_map(text: str) -> SecretMap:
    """Parse a secret map from a JSON string: agent_type -> [[kv, env], ...] pairs."""
    raw: object = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("secret map must be a JSON object")
    secret_map: dict[str, list[tuple[str, str]]] = {}
    for key, entries in raw.items():
        if not isinstance(entries, list) or not all(
            isinstance(p, list) and len(p) == 2 for p in entries
        ):
            raise ValueError(
                f"secret map entry {key!r} must be a list of [kv, env] pairs"
            )
        secret_map[str(key)] = [(str(p[0]), str(p[1])) for p in entries]
    return secret_map


def load_secret_map(path: str) -> SecretMap:
    """Load a secret map from a JSON file at *path*."""
    return parse_secret_map(Path(path).read_text(encoding="utf-8"))


def resolve_config(
    agent_type: str, store: SecretStore, secret_map: SecretMap
) -> dict[str, object]:
    """Fetch entitled secrets for *agent_type*; omit missing (empty-string) values.

    Returns a flat dict keyed by the canonical env-var names agents' settings read,
    ready to be written into os.environ by kernel.bootstrap._apply_config().
    """
    config: dict[str, object] = {}
    for kv_name, env_name in secret_map.get(agent_type, []):
        value = store.get_secret(kv_name)
        if value:
            config[env_name] = value
    return config
