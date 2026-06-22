"""Shared master test helpers.

Agent: master
Role: load the real trading grant policy so master tests exercise the production
      pack file (and the substrate no longer knows agent types on its own).
External I/O: reads orchestration/packs/trading_grants.json.
"""

from __future__ import annotations

from pathlib import Path

from agents.master.grants import GrantPolicy, load_grant_policy
from agents.master.secret_map import SecretMap, load_secret_map

_PACKS = Path(__file__).resolve().parents[3] / "orchestration" / "packs"
TRADING_GRANTS_PATH = str(_PACKS / "trading_grants.json")
TRADING_SECRETS_PATH = str(_PACKS / "trading_secrets.json")


def trading_policy() -> GrantPolicy:
    """Load the real trading grant policy used by the deployed fleet."""
    return load_grant_policy(TRADING_GRANTS_PATH)


def trading_secret_map() -> SecretMap:
    """Load the real trading secret map used by the deployed fleet."""
    return load_secret_map(TRADING_SECRETS_PATH)
