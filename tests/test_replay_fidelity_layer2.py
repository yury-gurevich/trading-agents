"""S237 Layer 2: live inputs swapped for the cache's, one at a time, in a fixed order.

Agent: tooling
Role: prove the swap order, the chained stages and exact Jaccard values.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest
from tests.fidelity_fleet import FleetDay, fleet_graph
from tests.fidelity_fleet_data import HELD_ONLY, SESSIONS, TICKERS, window_days
from tests.fidelity_harness import (
    copy_export,
    edit_session,
    export,
    replay,
    rows,
    tiny_repo,
    write_cache,
)

if TYPE_CHECKING:
    from pathlib import Path

STEPS = [
    "0_live",
    "1_sip_volume",
    "2_no_fundamentals",
    "3_no_news",
    "4_no_earnings",
    "5_cache_bars",
]


class Fleet(NamedTuple):
    repo: Path
    export: Path
    cache: Path


@pytest.fixture(scope="module")
def fleet(tmp_path_factory: pytest.TempPathFactory) -> Fleet:
    """Two runs whose only input gap to the cache is IEX-thin volume."""
    root = tmp_path_factory.mktemp("fleet")
    repo, sha = tiny_repo(root / "repo")
    days = tuple(
        FleetDay(day, enriched=False, volume_share=0.5) for day in SESSIONS[:2]
    )
    graph = fleet_graph(days, git_sha=sha)
    cache = write_cache(root / "cache", (*TICKERS, HELD_ONLY))
    return Fleet(repo, export(graph, root / "export"), cache)


def _tickers(value: str) -> set[str]:
    return set(value.split())


def test_a7_only_the_volume_swap_moves_the_decisions(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01 / DL-233: IEX volume moves candidates; nothing after it does."""
    summary = replay(fleet.export, tmp_path / "out", fleet.repo, cache=fleet.cache)

    assert summary["layer2"]["skipped"] is False
    for session in SESSIONS[:2]:
        steps = [
            row
            for row in rows(tmp_path / "out", "layer2.csv")
            if row["session"] == session.isoformat()
        ]
        assert [row["step"] for row in steps] == STEPS
        first = _tickers(steps[0]["candidates"])
        swapped = _tickers(steps[1]["candidates"])
        assert swapped != first
        assert _tickers(steps[1]["candidates_entered"]) == swapped - first
        assert _tickers(steps[1]["candidates_left"]) == first - swapped
        assert steps[1]["unswapped_volume_bars"] == "0"
        for later in steps[2:]:
            for column in ("candidates", "recommendations", "approvals"):
                assert later[column] == steps[1][column]
            for column in ("candidates_entered", "candidates_left"):
                assert later[column] == ""
        for step in steps:
            members = _tickers(step["candidates"])
            union = first | members
            expected = len(first & members) / len(union) if union else 1.0
            assert float(step["candidates_jaccard"]) == expected
        assert float(steps[0]["candidates_jaccard"]) == 1.0
        assert float(steps[0]["approvals_jaccard"]) == 1.0


def test_layer2_is_skipped_and_said_so_without_a_cache(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01: without --cache there is no Layer 2, and the report says so."""
    summary = replay(fleet.export, tmp_path / "out", fleet.repo)

    assert summary["layer2"] == {
        "skipped": True,
        "reason": "no --cache given: Layer 2 needs the S235 replay cache",
    }
    assert not (tmp_path / "out" / "layer2.csv").exists()
    report = (tmp_path / "out" / "fidelity.md").read_text(encoding="utf-8")
    assert "Layer 2 skipped: no --cache given" in report


def test_a_ticker_the_cache_lacks_keeps_its_volume_and_is_counted(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01 / DL-233: a bar with no cache twin is counted, never invented."""
    cache = write_cache(tmp_path / "cache", TICKERS)

    replay(fleet.export, tmp_path / "out", fleet.repo, cache=cache)

    steps = [
        row
        for row in rows(tmp_path / "out", "layer2.csv")
        if row["session"] == SESSIONS[0].isoformat()
    ]
    assert steps[1]["unswapped_volume_bars"] == str(len(window_days(SESSIONS[0])))
    assert HELD_ONLY not in _tickers(steps[5]["candidates"])


def test_a_session_without_a_snapshot_has_no_layer2_rows(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01: Layer 2 replays only what the export stored."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    edit_session(
        export_dir, SESSIONS[1], lambda payload: payload["market"].update(snapshot=None)
    )

    summary = replay(export_dir, tmp_path / "out", fleet.repo, cache=fleet.cache)

    assert {row["session"] for row in rows(tmp_path / "out", "layer2.csv")} == {
        SESSIONS[0].isoformat()
    }
    assert summary["layer2"] == {"skipped": False, "sessions": 1}
