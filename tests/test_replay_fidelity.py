"""Tests for S237 replay fidelity outputs.

Agent: tooling
Role: prove layer summaries, causes, and clean-session verdict handling.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from scripts.replay_fidelity_compare import refuse_worktree_out, run_fidelity


def test_fidelity_reports_unexplained_clean_difference_as_fail(tmp_path: Path) -> None:
    """SCAN-IDM-01 / ANLZ-IDM-01 / PM-IDM-01: differences get one cause."""
    export = tmp_path / "export"
    out = tmp_path / "out"
    export.mkdir()
    _session(
        export / "sched-2026-09-25.json",
        deploy_sha="HEAD",
        live_confidence=0.91,
        replay_confidence=0.90,
    )

    summary = run_fidelity(export=export, cache=None, out=out, git_diff=_clean_diff)

    assert summary["verdict"] == "FAIL"
    assert summary["clean"]["pooled"]["causes"] == {"unexplained": 1}
    rows = list(csv.DictReader((out / "layer1.csv").open(encoding="utf-8")))
    confidence = next(row for row in rows if row["field"] == "confidence")
    assert confidence == {
        "cause": "unexplained",
        "field": "confidence",
        "live": "0.91",
        "match": "False",
        "replay": "0.9",
        "session": "2026-09-25",
        "stage": "analyst",
        "ticker": "AAA",
    }
    assert "verdict: FAIL" in (out / "fidelity.md").read_text(encoding="utf-8")


def test_code_changed_sessions_are_not_pooled(tmp_path: Path) -> None:
    """ANLZ-IDM-01 / LAW-02: non-clean sessions are reported beside the verdict."""
    export = tmp_path / "export"
    out = tmp_path / "out"
    export.mkdir()
    _session(
        export / "sched-2026-09-24.json",
        deploy_sha="abc123",
        live_confidence=0.91,
        replay_confidence=0.90,
    )

    summary = run_fidelity(
        export=export,
        cache=None,
        out=out,
        git_diff=lambda _sha: ("agents/analyst/domain/analyze.py",),
    )

    assert summary["verdict"] == "INSUFFICIENT"
    assert summary["clean"]["denominator"] == 0
    assert summary["non_clean"][0]["session"] == "2026-09-24"
    assert summary["non_clean"][0]["causes"] == {
        "code_changed:agents/analyst/domain/analyze.py": 1
    }


def test_replay_fidelity_refuses_out_inside_repo() -> None:
    """RPT-NEV-02: fidelity outputs stay outside the worktree."""
    with pytest.raises(ValueError, match="inside the worktree"):
        refuse_worktree_out(Path.cwd() / "fidelity")


def _session(
    path: Path,
    *,
    deploy_sha: str,
    live_confidence: float,
    replay_confidence: float,
) -> None:
    path.write_text(
        json.dumps(
            {
                "run_id": path.stem,
                "session": path.stem.removeprefix("sched-"),
                "deploy": {"sha": deploy_sha},
                "not_persisted": [],
                "scanner": {
                    "candidate_set": {"candidates": [{"ticker": "AAA", "rank": 1}]}
                },
                "analyst": {
                    "recommendation_set": {
                        "recommendations": [
                            {
                                "ticker": "AAA",
                                "action": "buy",
                                "confidence": live_confidence,
                                "technical_score": 0.8,
                                "suggested_stop_pct": 0.05,
                            }
                        ]
                    }
                },
                "pm": {
                    "order_intents": [
                        {
                            "ticker": "AAA",
                            "action": "buy",
                            "quantity": 1,
                            "stop_pct": 0.05,
                        }
                    ],
                    "rejections": [],
                },
                "replay": {
                    "scanner": {
                        "candidate_set": {"candidates": [{"ticker": "AAA", "rank": 1}]}
                    },
                    "analyst": {
                        "recommendation_set": {
                            "recommendations": [
                                {
                                    "ticker": "AAA",
                                    "action": "buy",
                                    "confidence": replay_confidence,
                                    "technical_score": 0.8,
                                    "suggested_stop_pct": 0.05,
                                }
                            ]
                        }
                    },
                    "pm": {
                        "order_intents": [
                            {
                                "ticker": "AAA",
                                "action": "buy",
                                "quantity": 1,
                                "stop_pct": 0.05,
                            }
                        ],
                        "rejections": [],
                    },
                },
                "execution": {"submitted": 1, "dropped": 0, "rejected": 0},
                "deliberation": {"vetoed_tickers": []},
                "fills": [{"ticker": "AAA", "status": "filled"}],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _clean_diff(_sha: str) -> tuple[str, ...]:
    return ()
