"""Master grant-policy loader tests.

Agent: master
Role: verify load_grant_policy reads and validates the pack grant-policy JSON.
External I/O: reads temp JSON files and the real trading_grants.json.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from agents.master.grants import load_grant_policy
from agents.master.tests.helpers import TRADING_GRANTS_PATH

if TYPE_CHECKING:
    from pathlib import Path

_EXPECTED_TYPES = {
    "scanner",
    "analyst",
    "portfolio_manager",
    "execution",
    "monitor",
    "reporter",
    "forecaster",
    "operator",
    "supervisor",
    "curator",
    "researcher",
    "provider",
}


def test_load_grant_policy_reads_trading_pack() -> None:
    """The real trading pack file loads with all 12 agent types and their caps."""
    policy = load_grant_policy(TRADING_GRANTS_PATH)
    assert set(policy) == _EXPECTED_TYPES
    assert "broker" in policy["execution"]
    assert "data_feeds" in policy["provider"]
    assert "llm" in policy["operator"]


def test_load_grant_policy_rejects_non_object_json(tmp_path: Path) -> None:
    """A JSON file whose top level is not an object is rejected."""
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_grant_policy(str(bad))


def test_load_grant_policy_rejects_non_object_entry(tmp_path: Path) -> None:
    """A policy entry that is not an object is rejected."""
    bad = tmp_path / "bad2.json"
    bad.write_text(json.dumps({"scanner": "nope"}), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_grant_policy(str(bad))
