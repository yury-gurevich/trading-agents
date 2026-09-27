"""Tests for S235 replay output safety and reporter metric delegation.

Agent: tooling
Role: verify deterministic artifacts stay outside the worktree and use reporter math.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from scripts.replay_outputs import (
    EquityPoint,
    performance_summary,
    refuse_worktree_out,
    write_replay_outputs,
)


def test_out_path_inside_worktree_is_refused(tmp_path: Path) -> None:
    """S235-A16: replay outputs cannot be written inside the source worktree."""
    worktree_out = Path.cwd() / "tmp-replay-out"

    with pytest.raises(ValueError, match="inside the worktree"):
        refuse_worktree_out(worktree_out)
    assert refuse_worktree_out(tmp_path / "out") == tmp_path / "out"


def test_outputs_are_byte_identical_and_reporter_metric_is_called(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S235-A9/A17/A18: artifacts are deterministic and returns use reporter code."""
    points = (EquityPoint(date(2020, 1, 2), 100_000, 50_000),)
    calls: list[object] = []

    def fake_performance(
        observed: object, spy_closes: object, *, rolling_sessions: int
    ) -> dict[str, object]:
        calls.append((observed, spy_closes, rolling_sessions))
        return {"ok": True}

    monkeypatch.setattr(
        "scripts.replay_outputs.calculate_performance", fake_performance
    )
    assert performance_summary(points, {date(2020, 1, 2): 300.0}) == {"ok": True}
    assert calls == [(points, {date(2020, 1, 2): 300.0}, 20)]

    out = tmp_path / "cache" / "run"
    write_replay_outputs(
        out,
        points,
        ({"date": "2020-01-03", "ticker": "AAA", "side": "buy"},),
        ({"date": "2020-01-02", "expired": 0},),
        {"performance": {"ok": True}, "absent_inputs": {"sentiment": 1}},
    )
    first = {path.name: path.read_bytes() for path in sorted(out.iterdir())}
    write_replay_outputs(
        out,
        points,
        ({"date": "2020-01-03", "ticker": "AAA", "side": "buy"},),
        ({"date": "2020-01-02", "expired": 0},),
        {"performance": {"ok": True}, "absent_inputs": {"sentiment": 1}},
    )
    second = {path.name: path.read_bytes() for path in sorted(out.iterdir())}

    assert first == second
    assert json.loads((out / "summary.json").read_text())["absent_inputs"] == {
        "sentiment": 1
    }
