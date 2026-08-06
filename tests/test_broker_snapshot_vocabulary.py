"""Broker snapshot vocabulary tests.

Agent: kernel
Role: prove S161 BrokerPositionSnapshot account props are declared and guarded.
External I/O: reads the trading graph vocabulary pack.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kernel.graph_vocabulary import Vocabulary, VocabularyError

ROOT = Path(__file__).resolve().parents[1]
_PACK = ROOT / "orchestration" / "packs" / "trading_graph_vocabulary.json"


def test_broker_position_snapshot_account_props_are_declared_and_guarded() -> None:
    """EXEC-IDN-03 / DL-70: S161 account snapshot props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(json.loads(_PACK.read_text(encoding="utf-8")))
    props = {
        "run_id": "sched-2026-08-06",
        "status": "fresh",
        "created_at": "2026-08-06T00:00:00+00:00",
        "holding_count": 1,
        "holdings": [],
        "account_status": "fresh",
        "account_cash_cents": -10496677,
        "account_equity_cents": 10404269,
        "account_buying_power_cents": 16535900,
    }

    vocabulary.check_node("BrokerPositionSnapshot", props=props)
    with pytest.raises(VocabularyError, match="undeclared properties"):
        vocabulary.check_node(
            "BrokerPositionSnapshot",
            props={**props, "account_equity": "104042.69"},
        )
