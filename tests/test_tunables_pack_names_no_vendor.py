"""Tunables pack vendor ownership guards.

Agent: tooling
Role: verify that the LLM pack alone declares vendors and other tunables remain.
External I/O: committed JSON only.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TUNABLES = json.loads(
    (ROOT / "orchestration/packs/trading_tunables.json").read_text("utf-8")
)
LLM = json.loads((ROOT / "orchestration/packs/trading_llm.json").read_text("utf-8"))


def test_no_tunables_entry_carries_the_vendor_key_of_its_app() -> None:
    """DL-327: each app's vendor key belongs to the LLM pack alone."""
    assert len(LLM["apps"]) == 5
    for app, key in LLM["apps"].items():
        assert key not in TUNABLES["apps"].get(app, {})


def test_no_tunables_key_names_a_vendor() -> None:
    """DL-327: no tunables entry may introduce another vendor declaration."""
    keys = [key for entry in TUNABLES["apps"].values() for key in entry]
    assert keys
    assert not any(key.endswith("_LLM_PROVIDER") for key in keys)


def test_the_deliberators_keep_every_other_tunable() -> None:
    """DL-327: removing vendor keys preserves every other deliberator tunable."""
    assert sorted(TUNABLES["apps"]["deliberator-manager"]) == [
        "DELIBERATOR_DEBATE_CONCURRENCY",
        "DELIBERATOR_EFFORT",
        "DELIBERATOR_REQUEST_TIMEOUT_SECONDS",
    ]
    for app in ("deliberator-proponent", "deliberator-opponent"):
        assert sorted(TUNABLES["apps"][app]) == [
            "DELIBERATOR_EFFORT",
            "DELIBERATOR_REQUEST_TIMEOUT_SECONDS",
        ]


def test_the_packs_note_records_the_move() -> None:
    """DL-327: the pack's own note records the move and its decision."""
    note = TUNABLES["_measured"]
    assert "the three DELIBERATOR_LLM_PROVIDER lines" in note
    assert "The vendor is changed in trading_llm.json, never here" in note
    assert "DL-327" in note
