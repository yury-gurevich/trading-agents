"""Shared master test helpers.

Agent: master
Role: load the real trading grant policy so master tests exercise the production
      pack file (and the substrate no longer knows agent types on its own).
External I/O: reads orchestration/packs/trading_grants.json.
"""

from __future__ import annotations

from pathlib import Path

from agents.master.grants import GrantPolicy, load_grant_policy

TRADING_GRANTS_PATH = str(
    Path(__file__).resolve().parents[3]
    / "orchestration"
    / "packs"
    / "trading_grants.json"
)


def trading_policy() -> GrantPolicy:
    """Load the real trading grant policy used by the deployed fleet."""
    return load_grant_policy(TRADING_GRANTS_PATH)
