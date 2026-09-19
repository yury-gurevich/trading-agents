"""Master fleet-preflight pack declaration tests.

Agent: master
Role: prove trading-pack readiness declarations include every dependency.
External I/O: reads committed pack JSON only.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.master.tests.helpers import TRADING_CREDENTIAL_TESTS_PATH


def test_every_trading_credential_probe_is_required() -> None:
    """MST-NEV-06: the twelve pack-declared credential probes are all required."""
    declaration = json.loads(Path(TRADING_CREDENTIAL_TESTS_PATH).read_text())
    assert isinstance(declaration, dict)
    entries = [
        entry for agent_entries in declaration.values() for entry in agent_entries
    ]

    assert len(entries) == 12
    assert all(entry["required"] is True for entry in entries)


def test_vocabulary_declares_fleet_preflight_and_its_properties() -> None:
    """MST-IDN-02: master-owned FleetPreflight is vocabulary-declared."""
    path = Path(TRADING_CREDENTIAL_TESTS_PATH).with_name(
        "trading_graph_vocabulary.json"
    )
    vocabulary = json.loads(path.read_text())

    assert "FleetPreflight" in vocabulary["labels"]
    assert set(vocabulary["properties"]["FleetPreflight"]) == {
        "checked_at",
        "passed",
        "failure_count",
        "failures",
        "agent_types_checked",
    }
