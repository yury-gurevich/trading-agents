"""Top-signal selection tests.

Agent: analyst
Role: verify signal extraction, weighted ranking, pillar-diverse selection, and caps.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.domain.signal_selection import (
    Signal,
    fundamental_signals,
    select_top_signals,
    technical_signals,
)

_WEIGHTS = {"technical": 0.50, "fundamental": 0.30}


def test_technical_signals_keeps_only_score_keys() -> None:
    metrics = {"rsi": 28.0, "rsi_score": 80.0, "indicators_available": 3.0}
    assert technical_signals(metrics) == [
        Signal(name="rsi", pillar="technical", score=80.0)
    ]


def test_fundamental_signals_drops_available_meta() -> None:
    metrics = {"pe": 80.0, "roe": 55.0, "fundamentals_available": 2.0}
    assert fundamental_signals(metrics) == [
        Signal(name="pe", pillar="fundamental", score=80.0),
        Signal(name="roe", pillar="fundamental", score=55.0),
    ]


def test_empty_input_selects_nothing() -> None:
    assert select_top_signals([], _WEIGHTS, slack=5.0, max_signals=5) == ()


def test_ranks_by_weighted_distance_from_neutral() -> None:
    signals = [
        Signal("weak", "technical", 55.0),  # |5|*0.5 = 2.5
        Signal("strong", "technical", 90.0),  # |40|*0.5 = 20.0
    ]
    selected = select_top_signals(signals, _WEIGHTS, slack=5.0, max_signals=2)
    assert [signal.name for signal in selected] == ["strong", "weak"]


def test_diversity_lifts_a_fresh_pillar_within_slack() -> None:
    # T1=20.0, T2=17.5, F1=13.5; with slack 5, F1 (+5=18.5) beats T2 (17.5) for slot 2.
    signals = [
        Signal("t1", "technical", 90.0),
        Signal("t2", "technical", 85.0),
        Signal("f1", "fundamental", 95.0),
    ]
    selected = select_top_signals(signals, _WEIGHTS, slack=5.0, max_signals=3)
    assert [signal.name for signal in selected] == ["t1", "f1", "t2"]


def test_no_diverse_candidate_falls_back_to_best() -> None:
    signals = [
        Signal("t1", "technical", 90.0),
        Signal("t2", "technical", 80.0),
    ]
    selected = select_top_signals(signals, _WEIGHTS, slack=5.0, max_signals=5)
    assert [signal.name for signal in selected] == ["t1", "t2"]


def test_caps_at_max_signals() -> None:
    signals = [Signal(f"t{i}", "technical", 90.0 - i) for i in range(6)]
    selected = select_top_signals(signals, _WEIGHTS, slack=0.0, max_signals=3)
    assert len(selected) == 3


def test_unknown_pillar_contributes_zero_and_ranks_last() -> None:
    signals = [
        Signal("known", "technical", 70.0),  # |20|*0.5 = 10.0
        Signal("mystery", "other", 100.0),  # weight missing -> 0.0
    ]
    selected = select_top_signals(signals, _WEIGHTS, slack=0.0, max_signals=2)
    assert [signal.name for signal in selected] == ["known", "mystery"]
