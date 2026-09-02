"""Vocabulary guard tests for deliberation and shared LLM audit records.

Agent: kernel
Role: prove S153 node properties are declared before the live guard sees them.
External I/O: reads the committed trading vocabulary pack.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kernel.graph_vocabulary import Vocabulary, VocabularyError

ROOT = Path(__file__).resolve().parents[1]
_PACK = ROOT / "orchestration" / "packs" / "trading_graph_vocabulary.json"


def _declaration() -> dict[str, object]:
    data = json.loads(_PACK.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_deliberation_run_props_are_declared_and_unknown_prop_fails() -> None:
    """DL-80 / DL-70: S153 DeliberationRun props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(_declaration())
    props = {
        "source_pm_run_id": "pm-1",
        "verdicts": {"AAPL": "uphold"},
        "vetoed_tickers": [],
        "debates": {"AAPL": {"verdict": "uphold"}},
        "narrative": "AAPL: uphold",
        "transcript": [{"ticker": "AAPL", "role": "defender"}],
        "role_models": {"defender": "claude-opus-5"},
        "max_rounds": 2,
        "real_debate_count": 1,
        "failed_open_count": 0,
        "orphaned_reply_count": 0,
        "failed_open_tickers": [],
        "failed_open_reason": "",
        "created_at": "2026-08-01T00:00:00+00:00",
    }

    vocabulary.check_node("DeliberationRun", props=props)
    planted = _declaration()
    properties = planted["properties"]
    assert isinstance(properties, dict)
    declared = properties["DeliberationRun"]
    assert isinstance(declared, list)
    declared.remove("failed_open_count")
    with pytest.raises(VocabularyError, match="failed_open_count"):
        Vocabulary.from_mapping(planted).check_node("DeliberationRun", props=props)
    with pytest.raises(VocabularyError, match="undeclared properties"):
        vocabulary.check_node("DeliberationRun", props={**props, "vetoed_tikcers": []})


def test_llmcall_props_are_declared_and_unknown_prop_fails() -> None:
    """ADR-0020 / DL-70: shared LLMCall props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(_declaration())
    props = {
        "calling_agent": "deliberator-manager",
        "correlation_id": "pm-1:AAPL:judge",
        "model": "claude-opus-5",
        "prompt_hash": "abc",
        "response_hash": "def",
        "stop_reason": "end_turn",
        "tokens_in": 10,
        "tokens_out": 3,
        "latency_ms": 25,
        "created_at": "2026-08-01T00:00:00+00:00",
    }

    vocabulary.check_node("LLMCall", props=props)
    with pytest.raises(VocabularyError, match="undeclared properties"):
        vocabulary.check_node("LLMCall", props={**props, "calling_agnet": "x"})


def test_execution_run_deliberation_posture_props_are_declared() -> None:
    """EXEC-OUT-09 / DL-70: ExecutionRun posture props are vocabulary-declared."""
    vocabulary = Vocabulary.from_mapping(_declaration())
    props = {
        "source_pm_run_id": "pm-1",
        "submitted": 1,
        "rejected": 0,
        "skipped": 0,
        "deliberation_status": "applied_failed_open",
        "deliberation_posture": "advisory",
        "deliberation_blocked_count": 0,
    }

    vocabulary.check_node("ExecutionRun", props=props)
    with pytest.raises(VocabularyError, match="deliberation_postuer"):
        vocabulary.check_node(
            "ExecutionRun", props={**props, "deliberation_postuer": "advisory"}
        )
