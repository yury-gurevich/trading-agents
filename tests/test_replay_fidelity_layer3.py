"""S237 Layer 3: from PM approval to fill, counted from the live record only.

Agent: tooling
Role: prove the approval, veto, drop and fill counts read the live shapes.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_layer3 import layer3_row
from tests.fidelity_fleet import FleetDay, fleet_graph, pm_node
from tests.fidelity_fleet_data import SESSIONS
from tests.fidelity_fleet_outcomes import deliberate, execute
from tests.fidelity_harness import export, replay, rows, tiny_repo

from contracts.portfolio_manager import OrderIntentSet

if TYPE_CHECKING:
    from pathlib import Path

_DROP = "unfilled at session end"


def _fill(ticker: str, **props: Any) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "side": "buy",
        "status": "pending",
        "source_run_id": "pm-run-live",
        **props,
    }


def test_a8_layer3_counts_approvals_vetoes_drops_and_fills() -> None:
    """DLIB-OUT-02 / EXEC-OUT-07 / EXEC-STA-05: four counts from one session."""
    session = {
        "session": "2026-10-01",
        "pm": {
            "key": "pm-run-live",
            "order_intents": [
                {"ticker": ticker, "action": "buy"} for ticker in ("A", "B", "C", "D")
            ],
            "rejections": [],
        },
        "deliberation": {
            "verdicts": {
                "A": "overturn",
                "B": "overturn",
                "C": "uphold",
                "D": "revise",
            },
            "vetoed_tickers": ["A", "B", "D"],
        },
        "execution": {"submitted": 2, "rejected": 0, "skipped": 2},
        "fills": [
            _fill("C", broker_status="filled"),
            _fill("D", drop_reason=_DROP),
        ],
    }

    assert layer3_row(session) == {
        "session": "2026-10-01",
        "approved_buy": 4,
        "approved_sell": 0,
        "vetoed": 2,
        "submitted": 2,
        "execution_rejected": 0,
        "execution_skipped": 2,
        "filled": 1,
        "partial": 0,
        "broker_rejected": 0,
        "dropped": 1,
        "pending": 0,
    }


def test_layer3_reads_the_live_fill_shape_end_to_end(tmp_path: Path) -> None:
    """EXEC-STA-05 / DLIB-OUT-04: broker_status is the outcome; source_run_id links."""
    repo, sha = tiny_repo(tmp_path / "repo")
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha=sha)
    pm = pm_node(graph, f"sched-{SESSIONS[0].isoformat()}")
    approved = [
        intent.ticker
        for intent in OrderIntentSet.model_validate(
            pm.props["order_intent_set"]
        ).approved
    ]
    assert len(approved) >= 6
    deliberate(
        graph,
        pm,
        {
            approved[0]: "overturn",
            approved[1]: "overturn",
            approved[2]: "revise",
            approved[3]: "uphold",
        },
    )
    execute(
        graph,
        pm,
        {
            approved[2]: "filled",
            approved[3]: "dropped",
            approved[4]: "rejected",
            approved[5]: "pending",
        },
    )

    replay(export(graph, tmp_path / "export"), tmp_path / "out", repo)

    (row,) = rows(tmp_path / "out", "layer3.csv")
    assert row == {
        "session": SESSIONS[0].isoformat(),
        "approved_buy": str(len(approved)),
        "approved_sell": "0",
        "vetoed": "2",
        "submitted": "4",
        "execution_rejected": "0",
        "execution_skipped": str(len(approved) - 4),
        "filled": "1",
        "partial": "0",
        "broker_rejected": "1",
        "dropped": "1",
        "pending": "1",
    }
